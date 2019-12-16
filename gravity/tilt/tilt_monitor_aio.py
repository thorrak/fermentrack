#!/usr/bin/python

import os, sys
import time, datetime, getopt, pid
from typing import List, Dict
import asyncio
# import argparse, re
import aioblescan as aiobs

# done before importing django app as it does setup
import tilt_monitor_utils

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

from gravity.tilt.TiltHydrometer import TiltHydrometer
import gravity.models

# import django.core.exceptions

tilt_monitor_utils.process_monitor_options()

verbose = tilt_monitor_utils.verbose
mydev = tilt_monitor_utils.bluetooth_device

#### The main loop

# Create a list of TiltHydrometer objects for us to use
tilts = {x: TiltHydrometer(x) for x in TiltHydrometer.tilt_colors}  # type: Dict[str, TiltHydrometer]

# Create the default
reload_objects_at = datetime.datetime.now() + datetime.timedelta(seconds=15)


def processBLEBeacon(data):
    # While I'm not a fan of globals, not sure how else we can store state here easily
    global verbose
    global reload_objects_at
    global tilts

    ev = aiobs.HCI_Event()
    xx = ev.decode(data)

    # To make things easier, let's convert the byte string to a hex string first
    if ev.raw_data is None:
        if verbose:
            print("Event has no raw_data\r\n")
        return False

    raw_data_hex = ev.raw_data.hex()

    if len(raw_data_hex) < 80:  # Very quick filter to determine if this is a valid Tilt device
        if verbose:
            print("Small raw_data_hex: {}\r\n".format(raw_data_hex))
        return False
    if "1370f02d74de" not in raw_data_hex:  # Another very quick filter (honestly, might not be faster than just looking at uuid below)
        if verbose:
            print("Missing key in raw_data_hex: {}\r\n".format(raw_data_hex))
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
        print("Tilt Payload (hex): {}\r\n".format(payload))

    color = TiltHydrometer.color_lookup(uuid)  # Map the uuid back to our TiltHydrometer object
    tilts[color].process_decoded_values(gravity, temp, rssi)  # Process the data sent from the Tilt

    # The Fermentrack specific stuff:
    reload = False
    if datetime.datetime.now() > reload_objects_at:
        # Doing this so that as time passes while we're polling objects, we still end up reloading everything
        reload = True
        reload_objects_at = datetime.datetime.now() + datetime.timedelta(seconds=30)

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
        print('Keyboard interrupt\r\n')
finally:
    if verbose:
        print('Closing event loop\r\n')
    btctrl.stop_scan_request()
    command = aiobs.HCI_Cmd_LE_Advertise(enable=False)
    btctrl.send_command(command)
    conn.close()
    event_loop.close()
