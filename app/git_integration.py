from git import Repo
import fermentrack_django.settings as settings
from constance import config  # For the explicitly user-configurable stuff
import environ

env = environ.Env()


def app_is_current(tagged_commits_only=False, branch_to_check=None):
    local_repo = Repo(path=settings.ROOT_DIR)
    remote_repo = local_repo.remote()
    local_commit = local_repo.commit()

    if not config.ALLOW_GIT_BRANCH_SWITCHING and settings.GIT_BRANCH != config.GIT_UPDATE_TYPE and not \
            (settings.GIT_BRANCH == 'docker-dev' and config.GIT_UPDATE_TYPE == 'dev'):
        # The branch is set to "master" and update type is "dev" or vice-versa
        return False

    if tagged_commits_only:
        # Functionality no longer exists, but leaving the code in case we reenable it later. This should generally never
        # be reached.
        tags = get_tag_info()
        return tags['latest_tag']['committed_datetime'] <= local_commit.committed_datetime
    else:
        # We don't want to upgrade if the local commit is newer than the remote commit (IE - we're doing development
        # on the local copy)
        remote_fetch = remote_repo.fetch()
        remote_commit = remote_fetch[0].commit
        return remote_commit.committed_datetime <= local_commit.committed_datetime


def get_local_remote_commit_info():
    local_repo = Repo(path=settings.ROOT_DIR)
    remote_repo = local_repo.remote()

    local_commit = local_repo.commit()
    remote_commit = remote_repo.fetch()[0].commit

    local_branch = local_repo.active_branch.name

    commit_dict = {'local': local_commit, 'remote': remote_commit, 'local_branch': local_branch, 'remote_branch': ''}
    return commit_dict


def get_remote_branch_info():
    local_repo = Repo(path=settings.ROOT_DIR)

    # Fetch remote branches to ensure we are up to date
    for remote in local_repo.remotes:
        remote.fetch()

    remote_repo = local_repo.remote()

    local_branch = local_repo.active_branch.name
    remote_branches = []

    for this_branch in remote_repo.refs:
        remote_branches.append(this_branch.remote_head)

    return {'local_branch': local_branch, 'remote_branches': remote_branches}


def get_tag_info():
    local_repo = Repo(path=settings.ROOT_DIR)

    # Fetch remote branches to ensure we are up to date
    for remote in local_repo.remotes:
        remote.fetch()

    tags = []
    latest_tag = None

    for this_tag in local_repo.tags:
        tag_data = {'name': this_tag.name, 'committed_datetime': this_tag.commit.committed_datetime,
                     'hexsha': this_tag.commit.hexsha}
        if latest_tag is None:
            latest_tag = tag_data
        elif latest_tag['committed_datetime'] < tag_data['committed_datetime']:
            latest_tag = tag_data
        tags.append(tag_data)

    return {'latest_tag': latest_tag, 'all_tags': tags}


def get_local_version_numbers() -> dict:
    # DOCKER_CONTAINER_VERSION is set in compose/production/django/start
    # ENV_DJANGO_VERSION is set in .envs/.production/.django
    # ENV_POSTGRES_VERSION is set in .envs/.production/.postgres
    versions = {'docker_container_version': env.int("DOCKER_CONTAINER_VERSION", default=1),
                'env_django_version': env.int("ENV_DJANGO_VERSION", default=-1),
                'env_postgres_version': env.int("ENV_POSTGRES_VERSION", default=-1),
                'use_docker': env.bool("USE_DOCKER", default=False), }
    return versions

# The following was used for testing during development
# if __name__ == "__main__":
#     branches = get_remote_branch_info()
#     up_to_date_tagged = app_is_current(True)
