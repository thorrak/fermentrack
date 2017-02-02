
from git import Repo
import brewpi_django.settings as settings


def local_and_remote_are_at_same_commit(repo, remote):
    local_commit = repo.commit()
    remote_commit = remote.fetch()[0].commit
    return local_commit.hexsha == remote_commit.hexsha


def app_is_current():
    local_repo = Repo(path=settings.BASE_DIR)
    remote_repo = local_repo.remote()

    return local_and_remote_are_at_same_commit(local_repo, remote_repo)



