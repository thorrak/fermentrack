#!/usr/bin/env bash

# Defaults
BRANCH="origin/master"
SILENT=0

# Help text
function usage() {
    echo "Usage: $0 [-h] [-b <branch name>]" 1>&2
    exit 1
}

while getopts ":b:sh" opt; do
  case ${opt} in
    b)
      BRANCH=${OPTARG}
      ;;
    s)
      SILENT=1  # Currently unused
      usage
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


# First, launch the virtualenv
source ~/venv/bin/activate  # Assuming the directory based on a normal install with Fermentrack-tools

# Given that this script can be called by the webapp proper, give it 2 seconds to finish sending a reply to the
# user if he/she initiated an upgrade through the webapp.
sleep 2s

# Next, kill the running Fermentrack instance using circus
circusctl stop &> /dev/null

# Pull the latest version of the script from GitHub
cd ~/fermentrack  # Assuming the directory based on a normal install with Fermentrack-tools
git pull
git reset --hard &> /dev/null
git checkout ${BRANCH}

# Install everything from requirements.txt
pip install -r requirements.txt --upgrade

# Migrate to create/adjust anything necessary in the database
python manage.py migrate

# Migrate to create/adjust anything necessary in the database
python manage.py collectstatic --noinput >> /dev/null


# Finally, relaunch the Fermentrack instance using circus
circusctl start &> /dev/null
