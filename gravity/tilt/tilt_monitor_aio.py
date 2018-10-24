#!/usr/bin/python

import os, sys
import time, datetime, getopt, pid
from typing import List, Dict
import asyncio
# import argparse, re
import aioblescan as aiobs


# In order to be able to use the Django ORM, we have to load everything else Django-related. Lets do that now.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fermentrack_django.settings")  # This is so Django knows where to find stuff.
sys.path.append(BASE_DIR)
os.chdir(BASE_DIR)  # This is so my local_settings.py gets loaded.
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()


from gravity.tilt.TiltHydrometer import TiltHydrometer
import gravity.models

# import django.core.exceptions



# Script Defaults
verbose = False         # Should the script print out what it's doing to the console
pidFileDir = "/tmp"     # Where the pidfile should be written out to
mydev = 0  # Default to /dev/hci0


def print_to_stderr(*objs):
    print("", *objs, file=sys.stderr)


try:
    opts, args = getopt.getopt(sys.argv[1:], "h:vp:d:l", ['help', 'verbose', 'pidfiledir=', 'device=', 'list'])
except getopt.GetoptError:
    print_to_stderr("Unknown parameter. Available options: --help, --verbose, " +
                    "--pidfiledir <directory> --device <device number>", "--list")
    sys.exit()


for o, a in opts:
    # print help message for command line options
    if o in ('-h', '--help'):
        print_to_stderr("\r\n Available command line options: ")
        print_to_stderr("--help: Print this help message")
        print_to_stderr("--verbose: Echo readings to the console")
        print_to_stderr("--pidfiledir <directory path>: Directory to store the pidfile in")
        print_to_stderr("--device <device number>: The number of the bluetooth device (the X in /dev/hciX)")
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

    # Allow the user to specify an alternative bluetooth device
    if o in ('-d', '--device'):
        if not os.path.exists("/dev/hci{}".format(a)):
            sys.exit('ERROR: Device /dev/hci{} does not exist!'.format(a))
        mydev = a

    # List out the colors currently configured in Fermentrack
    if o in ('-l', '--list'):
        try:
            dbDevices = gravity.models.TiltConfiguration.objects.all()
            print("=============== Tilt Hydrometers in Database ===============")
            if len(dbDevices) == 0:
                print("No configured devices found.")
            else:
                x = 0
                print("Configured Colors:")
                for d in dbDevices:
                    x += 1
                    print("  %d: %s" % (x, d.color))
            print("============================================================")
            exit()
        except (Exception) as e:
            sys.exit(e)


# check for other running instances of the Tilt monitor script that will cause conflicts with this instance
pidFile = pid.PidFile(piddir=pidFileDir, pidname="tilt_monitor_aio")
try:
    pidFile.create()
except pid.PidFileAlreadyLockedError:
    print_to_stderr("Another instance of the monitor script is running. Exiting.")
    exit(0)


#### The main loop

# Create a list of TiltHydrometer objects for us to use
tilts = {x: TiltHydrometer(x) for x in TiltHydrometer.tilt_colors}  # type: Dict[str, TiltHydrometer]
# Create a list of UUIDs to match against & make it easy to lookup color
uuids = [TiltHydrometer.tilt_colors[x].replace("-","") for x in TiltHydrometer.tilt_colors]  # type: List[str]
# Create the default
reload_objects_at = datetime.datetime.now() + datetime.timedelta(seconds=15)


def processBLEBeacon(data):
    # While I'm not a fan of globals, not sure how else we can store state here easily
    global opts
    global reload_objects_at
    global tilts
    global uuids

    ev = aiobs.HCI_Event()
    xx = ev.decode(data)

    # To make things easier, let's convert the byte string to a hex string first
    raw_data_hex = ev.raw_data.hex()

    if len(raw_data_hex) < 80:  # Very quick filter to determine if this is a valid Tilt device
        return False
    if "1370f02d74de" not in raw_data_hex:  # Another very quick filter (honestly, might not be faster than just looking at uuid below)
        return False

    # For testing/viewing raw announcements, uncomment the following
    # print("Raw data (hex) {}: {}".format(len(raw_data_hex), raw_data_hex))
    # ev.show(0)

    try:
        # Let's use some of the functions of aioblesscan to tease out the mfg_specific_data payload
        payload = ev.retrieve("Payload for mfg_specific_data")[0].val.hex()

        # ...and then dissect said payload into a UUID, temp, gravity, and rssi (which isn't actually rssi)
        uuid = payload[8:40]
        temp = int.from_bytes(bytes.fromhex(payload[40:44]), byteorder='big')
        gravity = int.from_bytes(bytes.fromhex(payload[44:48]), byteorder='big')
        # tx_pwr = int.from_bytes(bytes.fromhex(payload[48:49]), byteorder='big')
        # rssi = int.from_bytes(bytes.fromhex(payload[49:50]), byteorder='big')
        rssi = 0  # TODO - Fix this
    except:
        return

    if verbose:
        print("Tilt Payload (hex): {}".format(payload))

    color = TiltHydrometer.color_lookup(uuid)  # Map the uuid back to our TiltHydrometer object
    tilts[color].process_decoded_values(gravity, temp, rssi)  # Process the data sent from the Tilt

    # The Fermentrack specific stuff:
    reload = False
    if datetime.datetime.now() > reload_objects_at:
        # Doing this so that as time passes while we're polling objects, we still end up reloading everything
        reload = True
        reload_objects_at = datetime.datetime.now() + datetime.timedelta(seconds=15)

    for this_tilt in tilts:
        if tilts[this_tilt].should_save():
            tilts[this_tilt].save_value_to_fermentrack(verbose=verbose)

        if reload:  # Users editing/changing objects in Fermentrack doesn't signal this process so reload on a timer
            tilts[this_tilt].load_obj_from_fermentrack()


event_loop = asyncio.get_event_loop()

# First create and configure a raw socket
mysocket = aiobs.create_bt_socket(mydev)

# create a connection with the raw socket (Uses _create_connection_transport instead of create_connection as this now
# requires a STREAM socket) - previously was fac=event_loop.create_connection(aiobs.BLEScanRequester,sock=mysocket)
fac = event_loop._create_connection_transport(mysocket, aiobs.BLEScanRequester, None, None)
conn, btctrl = event_loop.run_until_complete(fac)  # Start the bluetooth control loop
btctrl.process=processBLEBeacon  # Attach the handler to the bluetooth control loop

# Begin probing
btctrl.send_scan_request()
try:
    event_loop.run_forever()
except KeyboardInterrupt:
    if verbose:
        print('Keyboard interrupt')
finally:
    if verbose:
        print('Closing event loop')
    btctrl.stop_scan_request()
    command = aiobs.HCI_Cmd_LE_Advertise(enable=False)
    btctrl.send_command(command)
    conn.close()
    event_loop.close()
