#!/usr/bin/python

# TODO - Figure out the best way to convert this to use sync_to_async calls
import os, sys
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

# Let's get sentry support going
from sentry_sdk import init, capture_exception
init('http://3a1cc1f229ae4b0f88a4c6f7b5d8f394:c10eae5fd67a43a58957887a6b2484b1@sentry.optictheory.com:9000/2')

import time, datetime, getopt, pid
from typing import List, Dict
import asyncio

# Initialize logging
import logging
LOG = logging.getLogger("tilt")
LOG.setLevel(logging.INFO)

# We're having environment issues - Check the environment before continuing
try:
    import aioblescan as aiobs
except:
    LOG.error("Aioblescan not installed - unable to run")
    exit(1)

try:
    import pkg_resources
    from packaging import version
except:
    LOG.error("Packaging not installed - unable to run")
    exit(1)

for package in pkg_resources.working_set:
    if package.project_name == 'aioblescan':
        # This is ridiculous but package.parsed_version doesn't return the right type of Version.
        if version.parse(package.parsed_version.public) < version.parse("0.2.6"):
            LOG.error("Incorrect aioblescan version installed - unable to run")
            exit(1)

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
            LOG.error("Event has no raw data")
        return False

    raw_data_hex = ev.raw_data.hex()

    if len(raw_data_hex) < 80:  # Very quick filter to determine if this is a valid Tilt device
        # if verbose:
        #     LOG.info("Small raw_data_hex: {}".format(raw_data_hex))
        return False
    if "1370f02d74de" not in raw_data_hex:  # Another very quick filter (honestly, might not be faster than just looking at uuid below)
        # if verbose:
        #     LOG.info("Missing key in raw_data_hex: {}".format(raw_data_hex))
        return False

    # For testing/viewing raw announcements, uncomment the following
    # print("Raw data (hex) {}: {}".format(len(raw_data_hex), raw_data_hex))
    # ev.show(0)

    try:
        mac_addr = ev.retrieve("peer")[0].val
    except:
        pass

    try:
        # Let's use some of the functions of aioblesscan to tease out the mfg_specific_data payload

        manufacturer_data = ev.retrieve("Manufacturer Specific Data")
        payload = manufacturer_data[0].payload
        payload = payload[1].val.hex()

        # ...and then dissect said payload into a UUID, temp, and gravity
        uuid = payload[4:36]
        temp = int.from_bytes(bytes.fromhex(payload[36:40]), byteorder='big')
        gravity = int.from_bytes(bytes.fromhex(payload[40:44]), byteorder='big')
        # tx_pwr isn't actually tx_pwr on the latest Tilts - I need to figure out what it actually is
        tx_pwr = int.from_bytes(bytes.fromhex(payload[44:46]), byteorder='big', signed=False)
        rssi = ev.retrieve("rssi")[-1].val

    except Exception as e:
        LOG.error(e)
        capture_exception(e)
        return

    if verbose:
        LOG.info("Tilt Payload (hex): {}".format(raw_data_hex))

    color = TiltHydrometer.color_lookup(uuid)  # Map the uuid back to our TiltHydrometer object
    tilts[color].process_decoded_values(gravity, temp, rssi)  # Process the data sent from the Tilt

    #print("Color {} - MAC {}".format(color, mac_addr))
    #print("Raw Data: `{}`".format(raw_data_hex))

    # The Fermentrack specific stuff:
    reload = False
    if datetime.datetime.now() > reload_objects_at:
        # Doing this so that as time passes while we're polling objects, we still end up reloading everything
        reload = True
        reload_objects_at = datetime.datetime.now() + datetime.timedelta(seconds=30)

    for this_tilt in tilts:
        if tilts[this_tilt].should_save():
            if verbose:
                LOG.info("Saving {} to Fermentrack".format(this_tilt))
            tilts[this_tilt].save_value_to_fermentrack(verbose=verbose)

        if reload:  # Users editing/changing objects in Fermentrack doesn't signal this process so reload on a timer
            if verbose:
                LOG.info("Loading {} from Fermentrack".format(this_tilt))
            tilts[this_tilt].load_obj_from_fermentrack()


event_loop = asyncio.get_event_loop()

# First create and configure a raw socket
try:
    mysocket = aiobs.create_bt_socket(mydev)
except OSError as e:
    LOG.error("Unable to create socket - {}".format(e))
    exit(1)

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
        LOG.info('Keyboard interrupt')
finally:
    if verbose:
        LOG.info('Closing event loop')
    btctrl.stop_scan_request()
    command = aiobs.HCI_Cmd_LE_Advertise(enable=False)
    btctrl.send_command(command)
    conn.close()
    event_loop.close()
