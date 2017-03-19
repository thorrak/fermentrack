#!/usr/bin/env bash

# Defaults
BRANCH="master"
SILENT=0

# Colors (for printinfo/error/warn below)
green=$(tput setaf 76)
red=$(tput setaf 1)
tan=$(tput setaf 3)
reset=$(tput sgr0)


# Help text
function usage() {
    echo "Usage: $0 [-h] [-b <branch name>]" 1>&2
    exit 1
}

printinfo() {
  printf "::: ${green}%s${reset}\n" "$@"
}


printwarn() {
 printf "${tan}*** WARNING: %s${reset}\n" "$@"
}


printerror() {
 printf "${red}*** ERROR: %s${reset}\n" "$@"
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


exec > >(tee -i upgrade.log)


printinfo "Triggering upgrade from branch ${BRANCH}"
# First, launch the virtualenv
source ~/venv/bin/activate  # Assuming the directory based on a normal install with Fermentrack-tools

# Given that this script can be called by the webapp proper, give it 2 seconds to finish sending a reply to the
# user if he/she initiated an upgrade through the webapp.
printinfo "Waiting 2 seconds for Fermentrack to send updates if triggered from the web..."
sleep 2s

# Next, kill the running Fermentrack instance using circus
printinfo "Stopping circus..."
circusctl stop &> upgrade.log

# Pull the latest version of the script from GitHub
printinfo "Updating from git..."
cd ~/fermentrack  # Assuming the directory based on a normal install with Fermentrack-tools
git fetch &> upgrade.log
git reset --hard &> upgrade.log
git checkout ${BRANCH}
git pull &> upgrade.log

# Install everything from requirements.txt
printinfo "Updating requirements via pip..."
pip install -r requirements.txt --upgrade &> upgrade.log

# Migrate to create/adjust anything necessary in the database
printinfo "Running manage.py migrate..."
python manage.py migrate &> upgrade.log

# Migrate to create/adjust anything necessary in the database
printinfo "Running manage.py collectstatic..."
python manage.py collectstatic --noinput >> /dev/null


# Finally, relaunch the Fermentrack instance using circus
printinfo "Relaunching circus..."
circusctl reloadconfig &> upgrade.log
circusctl start &> upgrade.log
printinfo "Complete!"
