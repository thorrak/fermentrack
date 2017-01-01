brewpi-script utils
===================

This directory contains various utilities to manage your BrewPi installation

updateFirmware.py
-----------------
This python script gets the latest firmware from GitHub and flashes it to your controller
Run it with `python updateFirmware.py`

flashDfu.py
-----------
This python script flashes a new binary to a Spark Core in DFU mode using dfu-util
It waits for a device in DFU mode and then flashes it. Run it with `python updateFirmware.py`
Command line options:
* `--file <file name>, -f <file name>` path to file to be flashed  
* `--multi, -m` wait for the next device in DFU mode, used to flash multiple devices

updateCron.sh
-------------
Bash script will update the CRON job that is used to start/restart/check BrewPi

installDependencies.sh
-----------------------
Bash script that installs/updates dependencies required by BrewPi through apt-get and pip

fixPermissions.sh
-----------------
Bash script that sets the correct owner and permissions for the files in the web directory and script directory

runAfterUpdate.sh
-----------------
Bash script that runs the 3 scripts above

testTerminal.py
---------------
Python script that connects to the controller based on settings in the config file.
It allows you to send strings to the controller and it decodes the log messages that are sent back.
Windows only. Takes a path to a config file as first argument, defaults to the default location.

wifiChecker.sh
--------------
Bash script that checks WiFi connectivity and tries to restart network services when the network is down.
Can be ran periodically by cron to ensure WiFi stays alive.



