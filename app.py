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
github_requester = github.MainClass.Github(github_token)


logging.getLogger().setLevel(logging.DEBUG)


def split_pr_url(url):
    splitted_url = url.split('/')
    repo_name = '{}/{}'.format(splitted_url[4], splitted_url[5])
    pr_number = int(splitted_url[7])

    return repo_name, pr_number


@app.route("/healthcheck")
def healthcheck():
    return 'ok'


@webhook.hook('pull_request')
def on_pull_request(data):
    manager = imhotep.repomanagers.RepoManager(
        tools=[
            RubocopLinter(imhotep.app.run),
            GolintLinter(imhotep.app.run),
            EslintLinter(imhotep.app.run)],
        executor=imhotep.app.run, cache_directory='/tmp',
        authenticated=True)

    repo, pr_number = split_pr_url(data['pull_request']['url'])

    logging.info([repo, pr_number])

    pr_info = imhotep.shas.get_pr_info(
        github_requester, repo, pr_number).to_commit_info()

    logging.info(pr_info)

    imhotep.app.Imhotep(
        requester=github_requester, repo_manager=manager, commit_info=pr_info,
        shallow_clone=False, pr_number=pr_number, repo_name=repo).invoke()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
