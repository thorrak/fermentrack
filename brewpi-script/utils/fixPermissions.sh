#!/bin/bash
# This file can be used to automatically fix the permissions of files in /home/brewpi and /var/www on a Linux system
# with a default BrewPi install

############
### Functions to catch/display errors during setup
############
warn() {
  local fmt="$1"
  command shift 2>/dev/null
  echo -e "$fmt\n" "${@}"
  echo -e "\n*** ERROR ERROR ERROR ERROR ERROR ***\n----------------------------------\nSee above lines for error message\nScript NOT completed\n"
}

die () {
  local st="$?"
  warn "$@"
  exit "$st"
}

# the script path will one dir above the location of this bash file
unset CDPATH
myPath="$( cd "$( dirname "${BASH_SOURCE[0]}")" && pwd )"
scriptPath="$(dirname "$myPath")"
webPath="/var/www"

echo -e "\n***** Fixing file permissions for $webPath *****"
sudo chown -R www-data:www-data "$webPath"||warn
sudo chmod -R g+rwx "$webPath"||warn
sudo find "$webPath" -type d -exec chmod g+rwxs {} \;||warn

echo -e "\n***** Fixing file permissions for $scriptPath *****"
sudo chown -R brewpi:brewpi "$scriptPath"||warn
sudo chmod -R g+rwx "$scriptPath"||warn
sudo find "$scriptPath" -type d -exec chmod g+s {} \;||warn

