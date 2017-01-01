#!/bin/bash
# Copyright 2013 BrewPi
# This file is part of BrewPi.

# BrewPi is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# BrewPi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with BrewPi. If not, see <http://www.gnu.org/licenses/>.

########################
### This script will install dependencies required by BrewPi through apt-get
########################

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

############
### Install required packages
############
echo -e "\n***** Installing/updating required packages... *****\n"
lastUpdate=$(stat -c %Y /var/lib/apt/lists)
nowTime=$(date +%s)
if [ $(($nowTime - $lastUpdate)) -gt 604800 ] ; then
    echo "last apt-get update was over a week ago. Running apt-get update before updating dependencies"
    sudo apt-get update||die
fi

sudo apt-get install -y apache2 libapache2-mod-php5 php5-cli php5-common php5-cgi php5 git-core build-essential python-dev python-pip git-core || die

echo -e "\n***** Installing/updating required python packages via pip... *****\n"

unset CDPATH
myPath="$( cd "$( dirname "${BASH_SOURCE[0]}")" && pwd )"
scriptPath="$(dirname "$myPath")"


sudo pip install -r "$scriptPath/requirements.txt" --upgrade
#sudo pip install pyserial psutil simplejson configobj gitpython --upgrade

echo -e "\n***** Done processing BrewPi dependencies *****\n"
