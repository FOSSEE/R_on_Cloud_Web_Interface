import requests
from urllib.parse import urljoin
import json
from hyper.contrib import HTTP20Adapter
from git import Repo
from R_on_Cloud.config import MAIN_REPO


def get_commits(file_path, main_repo=True):
    repo_path = MAIN_REPO + file_path
    """
    return: list of commits, which affected the files in filepath
    """
    repo = Repo(repo_path, search_parent_directories=True)
    commit_message = []
    #print(list(repo.iter_commits(paths =  file_path)))
    for commit in list(repo.iter_commits(paths=file_path)):
        commit_message.append((commit.message, commit.hexsha))
    return commit_message


def get_file(file_path, commit_sha, main_repo=False):

    repo_path = MAIN_REPO + file_path
    repo = Repo(repo_path, search_parent_directories=True)
    file_contents = repo.git.show('{}:{}'.format(commit_sha, file_path))
    return file_contents