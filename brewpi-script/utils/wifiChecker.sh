#!/bin/bash
### Wifi Checking/Re-Enabling script for Brewpi
### This checks every 10 minutes to see if the wifi connection is still active via a ping
### If not, it will re-enable the wlan0 interface
### Geo Van O, Jan 2014
### User-editable settings ###
# Total number of times to try and contact the router if first packet fails
MAX_FAILURES=3
# Time to wait between failed attempts contacting the router
INTERVAL=15
###  DO NOT EDIT BELOW HERE!  ###

### Check if we have root privs to run
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root: sudo ./wifiChecker.sh) ($(date))" 1>&2
   exit 1
fi

if [ "$1" = "checkinterfaces" ]; then
    ### Make sure auto wlan0 is added to /etc/network/interfaces, otherwise it causes trouble bringing the interface back up
    grep "auto wlan0" /etc/network/interfaces > /dev/null
    if [ $? -ne 0 ]; then
        printf '%s\n' 0a "auto wlan0" . w | ed -s /etc/network/interfaces
    fi
    exit 0
fi

fails=0
gateway=$(/sbin/ip route | grep -m 1 default | awk '{ print $3 }')
### Sometimes network is so hosed, gateway IP is missing from ip route
if [ -z "$gateway" ]; then
    echo "BrewPi: wifiChecker: Cannot find gateway IP. Restarting wlan0 interface... ($(date))" 1>&2
    /sbin/ifdown wlan0
    /sbin/ifup wlan0
    exit 0
fi

while [ $fails -lt $MAX_FAILURES ]; do
### Try pinging, and if host is up, exit
    ping -c 1 -I wlan0 "$gateway" > /dev/null
    if [ $? -eq 0 ]; then
        fails=0
        echo "BrewPi: wifiChecker: Successfully pinged $gateway ($(date))"
        break
    fi
### If that didn't work...
    let fails=fails+1
    if [ $fails -lt $MAX_FAILURES ]; then
        echo "BrewPi: wifiChecker: Attempt $fails to reach $gateway failed ($(date))" 1>&2
        sleep $INTERVAL
    fi
done

### Restart wlan0 interface
    if [ $fails -ge $MAX_FAILURES ]; then
        echo "BrewPi: wifiChecker: Unable to reach router. Restarting wlan0 interface... ($(date))" 1>&2
        /sbin/ifdown wlan0
        /sbin/ifup wlan0
    fi
