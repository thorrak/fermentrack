#!/usr/bin/python

import os, sys

# In order to be able to use the Django ORM, we have to load everything else Django-related. Lets do that now.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fermentrack_django.settings")  # This is so Django knows where to find stuff.
sys.path.append(BASE_DIR)
os.chdir(BASE_DIR)  # This is so my local_settings.py gets loaded.
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()



import time, datetime, getopt, pid
from beacontools import BeaconScanner, IBeaconFilter, IBeaconAdvertisement
from typing import List, Dict

from gravity.tilt.TiltHydrometer import TiltHydrometer

import gravity.models

import django.core.exceptions


# Script Defaults
verbose = False         # Should the script print out what it's doing to the console
pidFileDir = "/tmp"     # Where the pidfile should be written out to


def print_to_stderr(*objs):
    print("", *objs, file=sys.stderr)


try:
    opts, args = getopt.getopt(sys.argv[1:], "h:vp:l", ['help', 'verbose', 'pidfiledir=', 'list'])
except getopt.GetoptError:
    print_to_stderr("Unknown parameter. Available options: --help, --color <color name>, --verbose, " +
                    "--pidfiledir <directory>", "--list")
    sys.exit()


for o, a in opts:
    # print help message for command line options
    if o in ('-h', '--help'):
        print_to_stderr("\r\n Available command line options: ")
        print_to_stderr("--help: Print this help message")
        print_to_stderr("--verbose: Echo readings to the console")
        print_to_stderr("--pidfiledir <directory path>: Directory to store the pidfile in")
        print_to_stderr("--list: List Tilt colors that have been set up in Fermentrack")
        exit()

    # Echo additional information to the console
    if o in ('-v', '--verbose'):
        verbose = True

    # Specify where the pidfile is saved out to
    if o in ('-p', '--pidfiledir'):
        if not os.path.exists(a):
            sys.exit('ERROR: pidfiledir "%s" does not exist' % a)
        pidFileDir = a

    # List out the colors currently configured in Fermentrack
    if o in ('-l', '--list'):
        try:
            dbDevices = gravity.models.TiltConfiguration.objects.all()
            print("=============== Tilt Hydrometers in Database ===============")
            if len(dbDevices) == 0:
                print("No configured devices found.")
            else:
                x = 0
                print("Available Colors:")
                for d in dbDevices:
                    x += 1
                    print("  %d: %s" % (x, d.color))
            print("============================================================")
            exit()
        except (Exception) as e:
            sys.exit(e)





# check for other running instances of BrewPi that will cause conflicts with this instance
pidFile = pid.PidFile(piddir=pidFileDir, pidname="tilt_monitor")
try:
    pidFile.create()
except pid.PidFileAlreadyLockedError:
    print_to_stderr("Another instance of the monitor script is running. Exiting.")
    exit(0)

#### Code that's used during the main loop

def callback(bt_addr, rssi, packet, additional_info):
    # Although beacontools provides a device filter option, we're not going to use it as it doesn't currently allow
    # specifying a list of UUIDs (I don't think, at least). Instead, we'll filter here.
    if additional_info['uuid'] in uuids:
        color = TiltHydrometer.color_lookup(additional_info['uuid'])  # Map the uuid back to our TiltHydrometer object
        tilts[color].process_ibeacon_info(packet, rssi)  # Process the data sent from the Tilt
        if verbose:
            # If we're in 'verbose' mode, also go ahead and print out the data we received
            tilts[color].print_data()




#### The main loop

# Create a list of TiltHydrometer objects for us to use
tilts = {x: TiltHydrometer(x) for x in TiltHydrometer.tilt_colors}  # type: Dict[str, TiltHydrometer]
# Create a list of UUIDs to match against & make it easy to lookup color
uuids = [TiltHydrometer.tilt_colors[x] for x in TiltHydrometer.tilt_colors]  # type: List[str]


# Start the scanner (filtering is done in the callback)
scanner = BeaconScanner(callback)
scanner.start()

if verbose:
    print("Beginning to scan for Tilt Hydrometers")

# For now, we're reloading Tilt hydrometers every 15 seconds
reload_objects_at = datetime.datetime.now() + datetime.timedelta(seconds=15)
reload = False

while True:

    if datetime.datetime.now() > reload_objects_at:
        # Doing this so that as time passes while we're polling objects, we still end up reloading everything
        reload = True

    for this_tilt in tilts:
        if tilts[this_tilt].should_save():
            tilts[this_tilt].save_value_to_fermentrack(verbose=verbose)

        if reload:
            tilts[this_tilt].load_obj_from_fermentrack()

    # Now that all the tilts have been attended to, if reload was true, reset the reload timer
    if reload:
        reload_objects_at = datetime.datetime.now() + datetime.timedelta(seconds=15)
        reload = False

    time.sleep(1)

# This is unreachable, but leaving it here anyways
scanner.stop()
