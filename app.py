import os
import flask
import github_webhook
import imhotep.app
import imhotep.shas
import imhotep.repomanagers
import logging
from linter.rubocop.linter import Linter as RubocopLinter
from linter.golint.linter import Linter as GolintLinter
from linter.eslint.linter import Linter as EslintLinter
import github.MainClass

app = flask.Flask(__name__)
webhook = github_webhook.Webhook(app)

github_token = os.environ.get('GITHUB_PASSWORD')
github_client = github.MainClass.Github(github_token)


manager = imhotep.repomanagers.RepoManager(
    tools=[
        RubocopLinter(imhotep.app.run),
        GolintLinter(imhotep.app.run),
        EslintLinter(imhotep.app.run)],
    executor=imhotep.app.run, cache_directory='/tmp',
    authenticated=True)

logging.getLogger().setLevel(logging.DEBUG)


def split_pr_url(url):
    splitted_url = url.split('/')
    repo_name = '{}/{}'.format(splitted_url[4], splitted_url[5])
    pr_number = int(splitted_url[7])

    return repo_name, pr_number


def pr_as_issue(data):
    repo, pr_number = split_pr_url(
        data.get('pull_request', data['issue'])['url'])
    org, repo = repo.split('/')

    return github_client.get_organization(org).get_repo(repo).get_issue(
        pr_number)


def get_labels(data):
    return pr_as_issue(data).get_labels()


def add_label_to_pr(data, label):
    pr_as_issue(data).add_to_labels(label)


def delete_review_labels(data):
    for label in get_labels(data):
        if label.name.startswith('reviewed/'):
            pr_as_issue(data).remove_from_labels(label)


@app.route("/healthcheck")
def healthcheck():
    return 'ok'


@webhook.hook('pull_request_review')
def on_pull_request_review(data):
    delete_review_labels(data)
    if data['review']['state'] == 'approved':
        add_label_to_pr(data, 'reviewed/ready-to-merge')
    else:
        add_label_to_pr(data, 'reviewed/needs-work')


@webhook.hook('issue_comment')
def on_issue_comment(data):
    if not data['issue'].get('pull_request'):
        return

    repo, pr_number = split_pr_url(data['issue']['url'])

    if 'lgtm' in data['comment']['body'].lower():
        delete_review_labels(data)
        add_label_to_pr('reviewed/ready-to-merge')


@webhook.hook('pull_request')
def on_pull_request(data):
    repo, pr_number = split_pr_url(data['pull_request']['url'])

    logging.info([repo, pr_number])

    if '[wip]' in data['pull_request']['title'].lower():
        delete_review_labels(data)
        add_label_to_pr(data, 'reviewed/work-in-progress')
        return

    if data['action'] == 'synchronized' or data['action'] == 'opened':
        delete_review_labels(data)
        add_label_to_pr(data, 'reviewed/needs-review')
        pr_info = imhotep.shas.get_pr_info(
            github_client, repo, pr_number).to_commit_info()

        imhotep.app.Imhotep(
            requester=github_client, repo_manager=manager,
            commit_info=pr_info, shallow_clone=False, pr_number=pr_number,
            repo_name=repo).invoke()
    elif data['action'] == 'edited':
        review_label = None

        for label in get_labels(data):
            if label.name.startswith('reviewed/'):
                review_label = label.name

        if not review_label:
            add_label_to_pr(data, 'reviewed/needs-review')
        elif review_label == 'reviewed/work-in-progress':
            delete_review_labels(data)
            add_label_to_pr(data, 'reviewed/needs-review')



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
