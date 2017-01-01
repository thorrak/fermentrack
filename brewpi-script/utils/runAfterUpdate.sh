#!/bin/bash
# This script should be run after running the BrewPi updater. It will call 3 other bash scripts to:
# 1. Install required dependencies through apt-get
# 2. Update the BrewPi CRON job that starts/restarts the BrewPi python script
# 3. Fix the owner/permissions of the files in the web and script dir

# the script path will one dir above the location of this bash file
unset CDPATH
myPath="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
scriptPath="$myPath/.."

#!/usr/bin/env bash

# Delete old .pyc files and empty directories from script directory
printf "Cleaning up BrewPi script directory...\n"
NUM_PYC_FILES=$( find "$scriptPath" -name "*.pyc" | wc -l | tr -d ' ' )
if [ $NUM_PYC_FILES -gt 0 ]; then
    find "$scriptPath" -name "*.pyc" -delete
    printf "Deleted $NUM_PYC_FILES old .pyc files\n"
fi

NUM_EMPTY_DIRS=$( find "$scriptPath" -type d -empty | wc -l | tr -d ' ' )
if [ $NUM_EMPTY_DIRS -gt 0 ]; then
    find "$scriptPath" -type d -empty -delete
    printf "Deleted $NUM_EMPTY_DIRS empty directories\n"
fi


sudo bash "$myPath"/installDependencies.sh
sudo bash "$myPath"/updateCron.sh
sudo bash "$myPath"/fixPermissions.sh
