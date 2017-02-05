#!/usr/bin/env bash

# First, launch the virtualenv
source ~/venv/bin/activate  # Assuming the directory based on a normal install with brewpi-django-tools

# Next, kill the running brewpi-django instance using circus
# TODO - Kill the running brewpi-django instance using circus

# Pull the latest version of the script from GitHub
cd ~/brewpi-django  # Assuming the directory based on a normal install with brewpi-django-tools
git pull
git reset --hard
git checkout origin/master

# Install everything from requirements.txt
pip install -r requirements.txt --upgrade

# Migrate to create/adjust anything necessary in the database
./manage.py migrate


# Finally, relaunch the brewpi-django instance using circus
# TODO - Relaunch the brewpi-django instance using circus