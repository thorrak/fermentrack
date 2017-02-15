#!/usr/bin/env bash

# First, launch the virtualenv
source ~/venv/bin/activate  # Assuming the directory based on a normal install with Fermentrack-tools

# Given that this script can be called by the webapp proper, give it 3 seconds to finish sending a reply to the
# user if he/she initiated an upgrade through the webapp.
sleep 3s

# Next, kill the running Fermentrack instance using circus
circusctl stop

# Pull the latest version of the script from GitHub
cd ~/brewpi-django  # Assuming the directory based on a normal install with Fermentrack-tools
git pull
git reset --hard
# TODO - Allow for the specification of a branch when calling upgrade.sh (given we have the data in Fermentrack)
git checkout origin/master

# Install everything from requirements.txt
pip install -r requirements.txt --upgrade

# Migrate to create/adjust anything necessary in the database
./manage.py migrate

# Migrate to create/adjust anything necessary in the database
./manage.py collectstatic --noinput >> /dev/null


# Finally, relaunch the Fermentrack instance using circus
circusctl start
