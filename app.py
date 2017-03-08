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
        data.get('pull_request', data.get('issue'))['url'])
    org, repo = repo.split('/')

    return github_client.get_organization(org).get_repo(repo).get_issue(
        pr_number)


def get_labels(data):
    return pr_as_issue(data).get_labels()


def add_label_to_pr(data, label):
    pr_as_issue(data).add_to_labels(label)


def set_review_label(data, target):
    found = False
    target = 'reviewed/{}'.format(target)

    for label in get_labels(data):
        if label.name.startswith('reviewed/') and not \
           label.name.endswith('delayed'):
            if label == target:
                found = True
            else:
                pr_as_issue(data).remove_from_labels(label)

    if not found:
        add_label_to_pr(data, target)


@app.route("/healthcheck")
def healthcheck():
    return 'ok'


@webhook.hook('pull_request_review')
def on_pull_request_review(data):
    if data['review']['state'] == 'approved':
        set_review_label(data, 'ready-to-merge')
    else:
        set_review_label(data, 'needs-work')


@webhook.hook('issue_comment')
def on_issue_comment(data):
    if not data['issue'].get('pull_request'):
        return

    repo, pr_number = split_pr_url(data['issue']['url'])

    if 'lgtm' in data['comment']['body'].lower():
        set_review_label(data, 'ready-to-merge')


@webhook.hook('pull_request')
def on_pull_request(data):
    def build_imhotep():
        repo, pr_number = split_pr_url(data['pull_request']['url'])
        logging.info([repo, pr_number])

        pr_info = imhotep.shas.get_pr_info(
            github_client, repo, pr_number).to_commit_info()

        return imhotep.app.Imhotep(
            requester=github_client, repo_manager=manager,
            commit_info=pr_info, shallow_clone=False, pr_number=pr_number,
            repo_name=repo)

    if '[wip]' in data['pull_request']['title'].lower() and \
       not data['action'] in ['labeled', 'unlabeled']:
        set_review_label(data, 'work-in-progress')
        return

    if data['action'] == 'synchronize' or data['action'] == 'opened':
        set_review_label(data, 'needs-review')
        build_imhotep().invoke()
    elif data['action'] == 'edited':
        review_label = None

        for label in get_labels(data):
            if label.name.startswith('reviewed/'):
                review_label = label.name

        if not review_label or review_label == 'reviewed/work-in-progress':
            set_review_label(data, 'needs-review')
            build_imhotep().invoke()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
