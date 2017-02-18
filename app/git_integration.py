
from git import Repo
import fermentrack_django.settings as settings


def local_and_remote_are_at_same_commit(repo, remote):
    local_commit = repo.commit()
    remote_fetch = remote.fetch()
    remote_commit = remote_fetch[0].commit
    # We don't want to upgrade if the local commit is newer than the remote commit (IE - we're doing development
    # on the local copy)
    return remote_commit.committed_datetime >= local_commit.committed_datetime
    # return local_commit.hexsha == remote_commit.hexsha


def app_is_current():
    local_repo = Repo(path=settings.BASE_DIR)
    remote_repo = local_repo.remote()

    return local_and_remote_are_at_same_commit(local_repo, remote_repo)


def get_local_remote_commit_info():
    local_repo = Repo(path=settings.BASE_DIR)
    remote_repo = local_repo.remote()

    local_commit = local_repo.commit()
    remote_commit = remote_repo.fetch()[0].commit

    local_branch = local_repo.active_branch.name

    commit_dict = {'local': local_commit, 'remote': remote_commit, 'local_branch': local_branch, 'remote_branch': ''}
    return commit_dict
