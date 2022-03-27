#!/usr/bin/env bash

# Defaults
BRANCH="master"
SILENT=0
TAG=""
SCRIPTPATH="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
FORCE_UPGRADE=0
USE_DOCKER=0

# We don't want to execute multiple upgrades at once, so use a lockfile to signify if an upgrade is in progress.
LOCKFILE="${SCRIPTPATH}/upgrade_lock"
if test -f "LOCKFILE"; then
  echo "$LOCKFILE exists - upgrade is already in progress. Delete $LOCKFILE to continue."
  exit 1
fi

touch "${LOCKFILE}"


# Colors (for printinfo/error/warn below)
green=$(tput setaf 76)
red=$(tput setaf 1)
tan=$(tput setaf 3)
reset=$(tput sgr0)


# Help text
function usage() {
    echo "Usage: $0 [-h] [-s] [-f] [-b <branch name>] [-t <tag name>]" 1>&2
    echo "-h: Help - Displays this text" 1>&2
    echo "-s: Silent - (currently unused)" 1>&2
    echo "-f: Force GitHub Update - Performs a hard reset when updating" 1>&2
    exit 1
}

printinfo() {
    if [ ${SILENT} -eq 0 ]
    then
      printf "::: ${green}%s${reset}\n" "$@"
      printf "::: ${green}%s${reset}\n" "$@" >> log/upgrade.log
    fi
}


printwarn() {
    if [ ${SILENT} -eq 0 ]
    then
        printf "${tan}*** WARNING: %s${reset}\n" "$@"
        printf "${tan}*** WARNING: %s${reset}\n" "$@" >> log/upgrade.log
    fi
}


printerror() {
    if [ ${SILENT} -eq 0 ]
    then
        printf "${red}*** ERROR: %s${reset}\n" "$@"
        printf "${red}*** ERROR: %s${reset}\n" "$@" >> log/upgrade.log
    fi
}


while getopts ":b:t:fdsh" opt; do
  case ${opt} in
    b)
      BRANCH=${OPTARG}
      ;;
    t)
      TAG=${OPTARG}
      ;;
    s)
      SILENT=1  # Currently unused
      usage
      ;;
    f)
      FORCE_UPGRADE=1
      ;;
    d)
      # If this upgrade is taking place from a dockerized install, then we need to do things slightly differently
      USE_DOCKER=1
      ;;
    h)
      usage
      exit 1
      ;;
    \?)
      echo "Invalid option: -$OPTARG" >&2
      usage
      exit 1
      ;;
  esac
done

shift $((OPTIND-1))



stop_supervisord () {
#  supervisorctl stop all
}


reload_supervisord () {
  supervisorctl reread
#  supervisorctl update
  supervisorctl restart
}


start_supervisord () {
#  supervisorctl start all
}


rm log/upgrade.log


printinfo "Triggering upgrade from branch ${BRANCH}"

#if [ ${USE_DOCKER} -eq 0 ]
#then
#  # For non-docker installs, we need to launch the virtualenv
#  source ~/venv/bin/activate  # Assuming the directory based on a normal install with Fermentrack-tools
#fi

# Given that this script can be called by the webapp proper, give it 2 seconds to finish sending a reply to the
# user if he/she initiated an upgrade through the webapp.
printinfo "Waiting 1 second for Fermentrack to send updates if triggered from the web..."
sleep 1s

# Next, kill the running Fermentrack instance using supervisord
printinfo "Stopping supervisord..."
stop_supervisord

# Pull the latest version of the script from GitHub
printinfo "Updating from git..."
cd "${SCRIPTPATH}/.." || exit  # Assuming this script is within the utils directory of a normal install

if [ ${FORCE_UPGRADE} -eq 0 ]
then
  git fetch --prune &>> log/upgrade.log
  git reset --hard &>> log/upgrade.log
else
  git fetch --all &>> log/upgrade.log
  git reset --hard @{u} &>> log/upgrade.log
fi


# If we have a tag set, use it
if [ "${TAG}" = "" ]
then
    git checkout ${BRANCH} &>> log/upgrade.log
else
    # Not entirely sure if we need -B for this, but leaving it here just in case
    git checkout tags/${TAG} -B ${BRANCH} &>> log/upgrade.log
fi

git pull &>> log/upgrade.log

# Install everything from requirements.txt
printinfo "Updating requirements via pip3..."
pip3 install --no-cache-dir -U -r requirements.txt --upgrade &>> log/upgrade.log

# Migrate to create/adjust anything necessary in the database
printinfo "Running manage.py migrate..."
python3 manage.py migrate &>> log/upgrade.log

# Migrate to create/adjust anything necessary in the database
printinfo "Running manage.py collectstatic..."
python3 manage.py collectstatic --noinput >> /dev/null


# Finally, relaunch the Fermentrack instance using supervisord
printinfo "Relaunching supervisord..."


reload_supervisord
start_supervisord
printinfo "Complete!"
rm "${LOCKFILE}"
