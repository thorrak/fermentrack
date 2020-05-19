#!/usr/bin/env bash

# Defaults
SILENT=0
CIRCUSCTL="python3 -m circus.circusctl --timeout 10"

# Colors (for printinfo/error/warn below)
green=$(tput setaf 76)
red=$(tput setaf 1)
tan=$(tput setaf 3)
reset=$(tput sgr0)



printinfo() {
    if [ ${SILENT} -eq 0 ]
    then
        printf "::: ${green}%s${reset}\n" "$@"
    fi
}


printwarn() {
    if [ ${SILENT} -eq 0 ]
    then
        printf "${tan}*** WARNING: %s${reset}\n" "$@"
    fi
}


printerror() {
    if [ ${SILENT} -eq 0 ]
    then
        printf "${red}*** ERROR: %s${reset}\n" "$@"
    fi
}


# Nuke the upgrade log before we attempt
touch log/upgrade.log
truncate --size=0 log/upgrade.log
exec > >(tee -i -a log/upgrade.log)


printinfo "Running fix_sqlite_for_django_2 management command"
# First, launch the virtualenv
source ~/venv/bin/activate  # Assuming the directory based on a normal install with Fermentrack-tools

# Given that this script can be called by the webapp proper, give it 2 seconds to finish sending a reply to the
# user if he/she initiated an upgrade through the webapp.
printinfo "Waiting 1 second for Fermentrack to send updates if triggered from the web..."
sleep 1s

# Next, kill the running Fermentrack instance using circus
printinfo "Stopping circus..."
$CIRCUSCTL stop &>> log/upgrade.log

# Run the management command
printinfo "Running fix_sqlite_for_django_2 management command"
python3 manage.py fix_sqlite_for_django_2 &>> log/upgrade.log


# Migrate to create/adjust anything necessary in the database
printinfo "Running manage.py migrate..."
python3 manage.py migrate &>> log/upgrade.log


# Finally, relaunch the Fermentrack instance using circus
printinfo "Relaunching circus..."
$CIRCUSCTL reloadconfig &>> log/upgrade.log
$CIRCUSCTL start &>> log/upgrade.log
printinfo "Complete!"
