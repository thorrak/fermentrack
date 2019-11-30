#!/usr/bin/python

# corbin dunn, oct 3, 2019.

import os, sys

# done before importing django app as it does setup
import tilt_monitor_utils

#from future.utils import raise_

import time, datetime, getopt, pid
from typing import List, Dict

from gravity.tilt.TiltHydrometer import TiltHydrometer

import gravity.models
import django.core.exceptions

import objc
import threading
from PyObjCTools import AppHelper
import CoreBluetooth
import Cocoa

# # Create a list of TiltHydrometer objects for us to use
tilts = {x: TiltHydrometer(x) for x in TiltHydrometer.tilt_colors}  # type: Dict[str, TiltHydrometer]
reload_objects_at = datetime.datetime.now() + datetime.timedelta(seconds=15)

################## tilt scanner; based off what I wrote for TiltBluetoothScanner.swift

class TiltBluetoothScanner(object):
    _central_manager: CoreBluetooth.CBCentralManager = None

    def __init__(self):
        self._central_manager = CoreBluetooth.CBCentralManager.alloc()
        self._central_manager.initWithDelegate_queue_options_(self, None, None)

    def __del__(self):    
        self.stopScaning()
    
    def startScanning(self):
        # Well, really starts scanning when bluetooth is on.
        self._checkBluetoothState()
    
    def stopScaning(self):
        if self._central_manager.isScanning:
            self._central_manager.stopScan()

    def _scanForPeripherals(self):
        # Do nil to find everything in range
        # note CBCentralManagerScanOptionAllowDuplicatesKey:False
        self._central_manager.scanForPeripheralsWithServices_options_(None, None)
    
    # CBCentralManagerDelegate delegate methods
    def centralManagerDidUpdateState_(self, manager):
        self._checkBluetoothState()
    
    def centralManager_didDiscoverPeripheral_advertisementData_RSSI_(self, manager, peripheral, advertisementData, rssi):

        #is it an iBeacon?
        # print(advertisementData)
        if advertisementData == None:
            return
        # advertisementData is an NSDictionary
        manufacturerData = advertisementData.objectForKey_("kCBAdvDataManufacturerData")
        if manufacturerData == None:
            return
        
        # see if we have an iBeacon
        if manufacturerData.length() != 25:
            return

        data = manufacturerData.bytes()
                
        if data[0] != 0x4C or data[1] != 0x00:
            return # { return nil } // Apple identifier

        if data[2] != 0x02:
            return #{ return nil } // iBeacon subtype identifier
        if data[3] != 0x15:
            return # { return nil } // Subtype length (fixed)
        
        uuid_data = data[4:20]
        # how to better convert bytes to a string?
        uuid = ""
        for i in range(16):
            uuid = uuid + "{0:x}".format(uuid_data[i])

        # is this a tilt?
        color = TiltHydrometer.color_lookup(uuid)  # Map the uuid back to our TiltHydrometer object
        if color == None:
            return

        temp = int.from_bytes(data[20:22], byteorder='big')
        gravity = int.from_bytes(data[22:24], byteorder='big')
        transmitPower = int.from_bytes(data[24:2], byteorder='big')

        global tilts
        global reload_objects_at

        tilts[color].process_decoded_values(gravity, temp, transmitPower)  # Process the data sent from the Tilt

        # This stuff below seems racy..

        # The Fermentrack specific stuff:
        reload = False
        if datetime.datetime.now() > reload_objects_at:
            # Doing this so that as time passes while we're polling objects, we still end up reloading everything
            reload = True
            reload_objects_at = datetime.datetime.now() + datetime.timedelta(seconds=30)

        for this_tilt in tilts:
            if tilts[this_tilt].should_save():
                tilts[this_tilt].save_value_to_fermentrack(verbose=tilt_monitor_utils.verbose)

            if reload:  # Users editing/changing objects in Fermentrack doesn't signal this process so reload on a timer
                tilts[this_tilt].load_obj_from_fermentrack()



    # End CBCentralManagerDelegate delegate methods.
    
    def _checkBluetoothState(self):
        state = self._central_manager.state()
        if state == CoreBluetooth.CBManagerStatePoweredOn:
            self._scanForPeripherals()


    # from Adafruit_python_bluefruit_le
    def _runMainRunLoop(self):
        # Create background thread to run user code.
        self._user_thread = threading.Thread(target=self._user_thread_main)
        self._user_thread.daemon = True
        self._user_thread.start()
        # Run main loop.  This call will never return!
        try:
            AppHelper.runConsoleEventLoop(installInterrupt=True)
        except KeyboardInterrupt:
            AppHelper.stopEventLoop()
            sys.exit(0)

    def _user_thread_main(self):
        tiltScanner.startScanning()

tiltScanner = TiltBluetoothScanner()
tiltScanner._runMainRunLoop() # doesn't return


