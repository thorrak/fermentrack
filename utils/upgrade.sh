#!/usr/bin/env bash

# Defaults
BRANCH="master"
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

echo "Triggering upgrade from branch ${BRANCH}"
# First, launch the virtualenv
source ~/venv/bin/activate  # Assuming the directory based on a normal install with Fermentrack-tools

# Given that this script can be called by the webapp proper, give it 2 seconds to finish sending a reply to the
# user if he/she initiated an upgrade through the webapp.
echo "Waiting 2 seconds for Fermentrack to send updates if triggered from the web..."
sleep 2s

# Next, kill the running Fermentrack instance using circus
echo "Stopping circus..."
circusctl stop &> /dev/null

# Pull the latest version of the script from GitHub
echo "Updating from git..."
cd ~/fermentrack  # Assuming the directory based on a normal install with Fermentrack-tools
git fetch &> /dev/null
git reset --hard &> /dev/null
git checkout ${BRANCH}
git pull &> /dev/null

# Install everything from requirements.txt
echo "Updating requirements via pip..."
pip install -r requirements.txt --upgrade

# Migrate to create/adjust anything necessary in the database
echo "Running manage.py migrate..."
python manage.py migrate

# Migrate to create/adjust anything necessary in the database
echo "Running manage.py collectstatic..."
python manage.py collectstatic --noinput >> /dev/null


# Finally, relaunch the Fermentrack instance using circus
echo "Relaunching circus..."
circusctl reloadconfig &> /dev/null
circusctl start &> /dev/null
echo "Complete!"
