#!/usr/bin/python
# Copyright 2012 BrewPi
# This file is part of BrewPi.

# BrewPi is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# BrewPi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with BrewPi.  If not, see <http://www.gnu.org/licenses/>.

import os
import socket
import sys
import time
import traceback

import urllib.parse as urllib

from distutils.version import LooseVersion

import json

# local imports
from scriptlibs.brewpiScriptConfig import BrewPiScriptConfig
from scriptlibs.BrewPiUtil import printStdErr, logMessage, asciiToUnicode
from scriptlibs import BrewPiUtil
from scriptlibs import brewpiVersion
from scriptlibs import pinList
from scriptlibs import expandLogMessage
from scriptlibs.backgroundserial import BackGroundSerial

# Settings will be read from controller, initialize with same defaults as controller
# This is mainly to show what's expected. Will all be overwritten on the first update from the controller

legacyHwVersion = "0.2.4"  # Minimum hardware version for 'legacy' branch support
developHwVersion = "0.4.0"  # Minimum hardware version for 'develop' branch support
compatibleHwVersion = legacyHwVersion  # Minimum supported version is 'legacy'
hwMode = ""  # Unused for now - either set to 'legacy' or 'modern'


def start_new_brew(config_obj, new_name, run):
    refresh_and_check(config_obj, run)  # Reload dbConfig from the database

    if config_obj.logging_status == config_obj.DATA_LOGGING_ACTIVE:
        logMessage(f"Notification: Started logging for beer '{urllib.unquote(new_name)}'.")
        return {'status': 0, 'statusMessage': f"Successfully switched to new brew '{urllib.unquote(new_name)}'. "}
    else:
        logMessage("ERROR: Data logging start request received, but not updated on the dbConfig object")
        return {'status': 1, 'statusMessage': "Logging not started on dbConfig object"}


def stop_logging(config_obj, run):
    refresh_and_check(config_obj, run)  # Reload dbConfig from the database

    if config_obj.logging_status == config_obj.DATA_LOGGING_STOPPED:
        logMessage("Data logging stopped")
        return {'status': 0, 'statusMessage': "Successfully stopped logging."}
    else:
        logMessage("ERROR: Data logging stop request received, but not updated on the dbConfig object")
        return {'status': 1, 'statusMessage': "Logging not stopped on dbConfig object"}


def pause_logging(config_obj, run):
    refresh_and_check(config_obj, run)  # Reload dbConfig from the database

    if config_obj.logging_status == config_obj.DATA_LOGGING_PAUSED:
        logMessage("Data logging paused")
        return {'status': 0, 'statusMessage': "Successfully paused logging."}
    else:
        logMessage("ERROR: Data logging pause request received, but not updated on the dbConfig object")
        return {'status': 1, 'statusMessage': "Logging not paused on dbConfig object"}


def resume_logging(config_obj, run):
    refresh_and_check(config_obj, run)  # Reload dbConfig from the database

    if config_obj.logging_status == config_obj.DATA_LOGGING_ACTIVE:
        logMessage(f"Notification: Successfully continued logging.")
        return {'status': 0, 'statusMessage': "Successfully continued logging. "}
    else:
        logMessage("ERROR: Data logging resume request received, but not updated on the dbConfig object")
        return {'status': 1, 'statusMessage': "Logging not resumed on dbConfig object"}


def refresh_and_check(config_obj, run):
    if not config_obj.refresh():
        run = 0

def BrewPiScript(config_obj):
    lcd_text = ['Script starting up', ' ', ' ', ' ']
    run = 1

    cs = dict(mode='b', beerSet=20.0, fridgeSet=20.0)  # Control Settings
    cc = dict()  # Control Constants
    cv = "{}"  # Control variables (json string, sent directly to browser without decoding)

    # listState = "", "d", "h", "dh" to reflect whether the list is up to date for installed (d) and available (h)
    device_list = dict(listState="", installed=[], available=[])
    
    if config_obj.status != BrewPiScriptConfig.STATUS_ACTIVE and \
            config_obj.status != BrewPiScriptConfig.STATUS_UNMANAGED:
        logMessage("This instance of BrewPi is currently disabled in the web interface. Reenable it and relaunch "
                   "this script. This instance will now exit.")
        time.sleep(1)
        exit(0)

    if config_obj.stdout_path:
        sys.stdout = open(config_obj.stdout_path, 'w')  # overwrite stdout file on script start
    if config_obj.stderr_path:
        sys.stderr = open(config_obj.stderr_path, 'a')  # append to stderr file

    # bytes are read from nonblocking serial into this buffer and processed when the buffer contains a full line.
    ser = BrewPiUtil.setupSerial(dbConfig=config_obj, time_out=0)
    
    if not ser:
        exit(1)
    
    if config_obj.active_beer_name:
        logMessage(f"Notification: Script started for beer '{config_obj.active_beer_name}'")
    else:
        logMessage("Notification: Script started, with no active beer being logged")
    
    # wait for 10 seconds to allow an Uno to reboot (in case an Uno is being used)
    time.sleep(10)
    
    logMessage("Checking software version on controller... ")
    hw_version = brewpiVersion.getVersionFromSerial(ser)
    hw_mode = "legacy"
    if hw_version is None:
        logMessage("Error: Cannot receive version number from controller. Your controller is either not programmed or "
                   "not responding.")
        lcd_text = ['Could not receive', 'version from controller', 'Please (re)program', 'your controller']
        exit(1)
    else:
        logMessage("Found " + hw_version.toExtendedString() + " on port " + ser.name + "\n")
        if LooseVersion(hw_version.toString()) < LooseVersion(compatibleHwVersion):
            # Completely incompatible. Unlikely to ever be triggered, as it requires pre-legacy code.
            logMessage(f"Warning: minimum BrewPi version compatible with this script is {compatibleHwVersion} but "
                       f"version number received is {hw_version.toString()}. Exiting.")
            exit(1)
        elif LooseVersion(hw_version.toString()) < LooseVersion(legacyHwVersion):
            # Compatible, but only with pre-legacy (!) code. This should never happen as legacy support is the "oldest"
            # codebase we provide for.
            # This will generally never happen given that we are setting compatible = legacy above
            logMessage(f"Warning: minimum BrewPi version compatible with this script for legacy support is "
                       f"{legacyHwVersion} but version number received is {hw_version.toString()}. Exiting.")
            exit(1)
        elif LooseVersion(hw_version.toString()) >= LooseVersion(developHwVersion):
            hw_mode = "modern"

        logMessage(f"BrewPi version received was {hw_version.toString()} which this script supports in "
                   f"'{hw_mode}' branch mode.")

    if int(hw_version.log) != int(expandLogMessage.getVersion()):
        logMessage("Warning: version number of local copy of logMessages.h " +
                   "does not match log version number received from controller." +
                   "controller version = " + str(hw_version.log) +
                   ", local copy version = " + str(expandLogMessage.getVersion()) +
                   ". This is generally a non-issue, as thus far log messages have only been added - not changed.")
    
    bg_ser = None
    
    if ser is not None:
        ser.flush()
    
        # set up background serial processing, which will continuously read data from serial and put whole lines in a 
        # queue
        bg_ser = BackGroundSerial(ser)
        bg_ser.start()
        # request settings from controller, processed later when reply is received
        bg_ser.writeln('s')  # request control settings cs
        bg_ser.writeln('c')  # request control constants cc
        bg_ser.writeln('v')  # request control variables cv
    
        # refresh the device list
        bg_ser.writeln("d{r:1}")  # request installed devices
        bg_ser.writeln("h{u:-1,v:1}")  # request available, but not installed devices
    
        # answer from controller is received asynchronously later.
    
    # create a listening socket to communicate with the web interface (socket for systems that support it, otherwise
    # an inetsocket (e.g. for windows))
    if sys.platform.startswith('win'):
        use_inet_socket = True
    else:
        use_inet_socket = config_obj.use_inet_socket
    
    if use_inet_socket:
        if config_obj.socket_host is None or config_obj.socket_port is None:
            logMessage('use_inet_socket is true, but socket_host or socket_port not set. Exiting.')
            exit(1)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        socket_port = config_obj.socket_port
        socket_host = config_obj.socket_host
        s.bind((socket_host, int(socket_port)))
        logMessage('Bound to TCP socket on port {}, interface {} '.format(int(socket_port), socket_host))
    else:
        if config_obj.socket_name is None:
            logMessage('use_inet_socket is false, but socket_name is not set. Exiting')
            exit(1)
        socket_file = BrewPiUtil.addSlash(BrewPiUtil.scriptPath()) + config_obj.socket_name
        if os.path.exists(socket_file):
            # if socket already exists, remove it
            os.remove(socket_file)
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(socket_file)  # Bind BEERSOCKET
        # set all permissions for socket
        os.chmod(socket_file, 0o0777)
    
    serial_check_interval = 0.5
    s.setblocking(True)  # set socket functions to be blocking
    s.listen(10)  # Create a backlog queue for up to 10 connections
    # blocking socket functions wait 'serialCheckInterval' seconds
    s.settimeout(serial_check_interval)
    
    prev_data_time = 0.0  # keep track of time between new data requests
    prev_time_out_req = prev_data_time  # Using this to fix the prevDataTime tracking
    prev_time_out = time.time()
    prev_lcd_update = time.time()
    prev_settings_update = time.time()
    

    output_temperature = True
    
    prev_temp_json = {
        "BeerTemp": 0,
        "FridgeTemp": 0,
        "BeerAnn": None,
        "FridgeAnn": None,
        "RoomTemp": None,
        "State": None,
        "BeerSet": 0,
        "FridgeSet": 0}

    def rename_temp_key(temp_key):
        rename = {
            "Log1Temp": "RoomTemp",  # Allows a configured OEM BrewPi to log room temp with Log1Temp
            "bt": "BeerTemp",
            "bs": "BeerSet",
            "ba": "BeerAnn",
            "ft": "FridgeTemp",
            "fs": "FridgeSet",
            "fa": "FridgeAnn",
            "rt": "RoomTemp",
            "s": "State",
            "t": "Time"}
        return rename.get(temp_key, temp_key)

    # At startup force synchronization of temperature format
    def sync_temp_format(control_constants):
        db_temp_format = config_obj.temp_format
    
        if control_constants['tempFormat'] != db_temp_format:
            # j{"tempFormat": "C"}
            settings_dict = {'tempFormat': config_obj.temp_format}
            bg_ser.writeln("j" + json.dumps(settings_dict))
            # TODO - Set min/max temp if necessary
    
    def trigger_refresh(read_values=False):
        # We want to keep the deviceList cache updated. Invalidate the cache, send a request to update the list to
        # the controller, then give it a few seconds to respond before raising socket.timeout & processing the
        # result.
    
        device_list['listState'] = ""  # invalidate local copy
        if read_values:
            bg_ser.writeln("d{r:1}")  # request installed devices
            bg_ser.writeln("h{u:-1,v:1}")  # request available, but not installed devices
        else:
            bg_ser.writeln("d{}")  # request installed devices
            bg_ser.writeln("h{u:-1}")  # request available, but not installed devices
        # Now, force a refresh of the device list (to keep it updated)
        time.sleep(2.5)  # We'll give the controller 5 seconds to respond
        raise socket.timeout

    while run:
        # Wait for incoming socket connections.
        # When nothing is received, socket.timeout will be raised after
        # serialCheckInterval seconds. Serial receive will be done then.
        # When messages are expected on serial, the timeout is raised 'manually'
        try:
            conn, addr = s.accept()
            conn.setblocking(True)
            # blocking receive, times out in serialCheckInterval
            message = conn.recv(4096)
            message = message.decode(encoding="cp437")
            if "=" in message:
                message_type, value = message.split("=", 1)
            else:
                message_type = message
                value = ""
            if message_type == "ack":  # acknowledge request
                conn.send(b'ack')
            elif message_type == "lcd":  # lcd contents requested
                if hw_mode == "modern":
                    # TODO - Emulate lcdText for modern controllers
                    pass
                conn.send(json.dumps(lcd_text).encode(encoding="cp437"))
            elif message_type == "getMode":  # echo cs['mode'] setting
                conn.send(cs['mode'].encode(encoding="cp437"))
            elif message_type == "getFridge":  # echo fridge temperature setting
                conn.send(json.dumps(cs['fridgeSet']).encode(encoding="cp437"))
            elif message_type == "getBeer":  # echo fridge temperature setting
                conn.send(json.dumps(cs['beerSet']).encode(encoding="cp437"))
            elif message_type == "getControlConstants":
                conn.send(json.dumps(cc).encode(encoding="cp437"))
            elif message_type == "getControlSettings":
                # TODO - See where/if we call getControlSettings (and fix the cs['profile'] response below)
                # if cs['mode'] == "p":
                #     profileFile = BrewPiUtil.addSlash(BrewPiUtil.scriptPath()) + 'settings/tempProfile.csv'
                #     with file(profileFile, 'r') as prof:
                #         cs['profile'] = prof.readline().split(",")[-1].rstrip("\n")
                cs['dataLogging'] = config_obj.logging_status
                conn.send(json.dumps(cs).encode(encoding="cp437"))
            elif message_type == "getControlVariables":
                conn.send(cv.encode(encoding="cp437"))
            elif message_type == "refreshControlConstants":
                bg_ser.writeln("c")
                raise socket.timeout
            elif message_type == "refreshControlSettings":
                bg_ser.writeln("s")
                raise socket.timeout
            elif message_type == "refreshControlVariables":
                bg_ser.writeln("v")
                raise socket.timeout
            elif message_type == "loadDefaultControlSettings":
                bg_ser.writeln("S")
                raise socket.timeout
            elif message_type == "loadDefaultControlConstants":
                bg_ser.writeln("C")
                raise socket.timeout
            elif message_type == "setBeer":  # new constant beer temperature received
                try:
                    new_temp = float(value)
                    cs['beerSet'] = round(new_temp, 2)
                except ValueError:
                    logMessage("Cannot convert temperature '" + value + "' to float")
                    continue
    
                cs['mode'] = 'b'
                # round to 2 dec, python will otherwise produce 6.999999999
                bg_ser.writeln("j{{mode:\"b\", beerSet:{}}}".format(cs['beerSet']))
                refresh_and_check(config_obj, run)  # Reload dbConfig from the database (in case we were using profiles)
                logMessage("Notification: Beer temperature set to {} degrees in web interface".format(cs['beerSet']))
                raise socket.timeout  # go to serial communication to update controller
    
            elif message_type == "setFridge":  # new constant fridge temperature received
                try:
                    new_temp = float(value)
                except ValueError:
                    logMessage("Cannot convert temperature '" + value + "' to float")
                    continue
    
                cs['mode'] = 'f'
                cs['fridgeSet'] = round(new_temp, 2)
                cmd = f'"j{{mode:"f", fridgeSet:{json.dumps(cs["fridgeSet"])}}}"'
                bg_ser.writeln(cmd)
                # Reload dbConfig from the database (in case we were using profiles)
                refresh_and_check(config_obj, run)  # Reload dbConfig from the database
                logMessage(f"Notification: Sending command {cmd} to set fridge temperature to {str(cs['fridgeSet'])} "
                           f"degrees from web interface")
                raise socket.timeout  # go to serial communication to update controller
    
            elif message_type == "setOff":  # cs['mode'] set to OFF
                cs['mode'] = 'o'
                bg_ser.writeln("j{mode:\"o\"}")
                refresh_and_check(config_obj, run)  # Reload dbConfig from the database (in case we were using profiles)
                logMessage("Notification: Temperature control disabled")
                raise socket.timeout
            elif message_type == "setParameters":
                # receive JSON key:value pairs to set parameters on the controller
                try:
                    decoded = json.loads(value)
                    bg_ser.writeln("j" + json.dumps(decoded))
                    if 'tempFormat' in decoded:
                        refresh_and_check(config_obj, run)  # Reload dbConfig from the database
                except ValueError:
                    logMessage("Error: invalid JSON parameter string received: " + value)
                raise socket.timeout
            elif message_type == "stopScript":  # exit instruction received. Stop script.
                # voluntary shutdown.
                log_message = "stopScript message received on socket. "
                run = 0
                log_message += "dbConfig in use - assuming device status was already properly updated "
                log_message += "to prevent automatic restart"
                logMessage(log_message)
                continue
            elif message_type == "quit":  # quit instruction received. Probably sent by another brewpi script instance
                logMessage("quit message received on socket. Stopping script.")
                run = 0
                # Leave dontrunfile alone.
                # This instruction is meant to restart the script or replace it with another instance.
                continue
            elif message_type == "eraseLogs":
                logMessage('eraseLogs is not implemented for this version of brewpi-script')
            elif message_type == "interval":  # new interval received
                refresh_and_check(config_obj, run)  # Reload dbConfig from the database
                # newInterval = int(value)
                new_interval = int(config_obj.data_point_log_interval)
                logMessage("Notification: Interval changed to " + str(new_interval) + " seconds")
            elif message_type == "startNewBrew":  # new beer name
                new_name = value
                result = start_new_brew(config_obj, new_name, run)
                conn.send(json.dumps(result).encode(encoding="cp437"))
            elif message_type == "pauseLogging":
                result = pause_logging(config_obj, run)
                conn.send(json.dumps(result).encode(encoding="cp437"))
            elif message_type == "stopLogging":
                result = stop_logging(config_obj, run)
                conn.send(json.dumps(result).encode(encoding="cp437"))
            elif message_type == "resumeLogging":
                result = resume_logging(config_obj, run)
                conn.send(json.dumps(result).encode(encoding="cp437"))
            elif message_type == "dateTimeFormatDisplay":
                logMessage('dateTimeFormatDisplay is not implemetned for this version of brewpi-script')
            elif message_type == "setActiveProfile":
                # We're using a dbConfig object to manage everything. We aren't being passed anything by Fermentrack
                logMessage("Setting controller to beer profile mode using database-configured profile")
                conn.send(b"Profile successfully updated")
                refresh_and_check(config_obj, run)  # Reload dbConfig from the database
                if cs['mode'] != 'p':
                    cs['mode'] = 'p'
                    bg_ser.writeln("j{mode:\"p\"}")
                    logMessage("Notification: Profile mode enabled")
                    raise socket.timeout  # go to serial communication to update controller
    
            elif message_type == "programController" or message_type == "programArduino":
                logMessage("programController action is not supported by this modified version of brewpi-script")
            elif message_type == "refreshDeviceList":
                # if value.find("readValues") != -1:
                trigger_refresh(True)
                # else:
                #     trigger_refresh(False)
            elif message_type == "getDeviceList":
                if device_list['listState'] in ["dh", "hd"]:
                    response = dict(board=hw_version.board,
                                    shield=hw_version.shield,
                                    deviceList=device_list,
                                    pinList=pinList.getPinList(hw_version.board, hw_version.shield))
                    conn.send(json.dumps(response).encode(encoding="cp437"))
                else:
                    # It's up to the web interface to track how often it requests an update
                    conn.send(b"device-list-not-up-to-date")
                    raise socket.timeout
            elif message_type == "getDashInfo":
                # This is a new messageType
                response = {"BeerTemp": prev_temp_json['BeerTemp'],
                            "FridgeTemp": prev_temp_json['FridgeTemp'],
                            "BeerAnn": prev_temp_json['BeerAnn'],
                            "FridgeAnn": prev_temp_json['FridgeAnn'],
                            "RoomTemp": prev_temp_json['RoomTemp'],
                            "State": prev_temp_json['State'],
                            "BeerSet": prev_temp_json['BeerSet'],
                            "FridgeSet": prev_temp_json['FridgeSet'],
                            "LogInterval": float(config_obj.data_point_log_interval),
                            "Mode": cs['mode']}
                conn.send(json.dumps(response).encode(encoding="cp437"))
            elif message_type == "applyDevice":
                # applyDevice is used to apply settings to an existing device (pin/OneWire assignment, etc.)
                try:
                    json.loads(value)  # load as JSON to check syntax
                except ValueError:
                    logMessage("Error: invalid JSON parameter string received: " + value)
                    continue
                logMessage("Received applyDevice request, updating to: {}".format(value))
                # bg_ser.writeln("U" + json.dumps(configStringJson))
                # No need to re-encode to JSON if we received valid JSON in the first place.
                bg_ser.writeln("U" + value)
    
                trigger_refresh(True)
            elif message_type == "writeDevice":
                # writeDevice is used to -create- "actuators" -- Specifically, (for now) buttons.
                try:
                    config_string_json = json.loads(value)  # load as JSON to check syntax
                except ValueError:
                    logMessage("Error: invalid JSON parameter string received: " + value)
                    continue
                bg_ser.writeln("d" + json.dumps(config_string_json))
    
                # We want to keep the deviceList cache updated. Invalidate the cache, send a request to update the list
                # to the controller, then give it a few seconds to respond before raising socket.timeout & processing
                # the result.
                trigger_refresh(True)
            elif message_type == "getVersion":
                if hw_version:
                    response = hw_version.__dict__
                    # replace LooseVersion with string, because it is not JSON serializable
                    response['version'] = hw_version.toString()
                else:
                    response = {}
                response_str = json.dumps(response)
                conn.send(response_str.encode(encoding="cp437"))
    
            elif message_type == "resetController":
                logMessage("Resetting controller to factory defaults")
                refresh_and_check(config_obj, run)  # Reload dbConfig from the database
                bg_ser.writeln("E{\"confirmReset\": true}")
                # request settings from controller, processed later when reply is received
                bg_ser.writeln('s')  # request control settings cs
                bg_ser.writeln('c')  # request control constants cc
                bg_ser.writeln('v')  # request control variables cv
                trigger_refresh(True)  # Refresh the device list cache (will also raise socket.timeout)
    
            elif message_type == "restartController":
                logMessage("Restarting controller")
                bg_ser.writeln("R")  # This tells the controller to restart
                time.sleep(3)  # We'll give bg_ser 3 seconds for it to send/kick in
                sys.exit(0)  # Exit BrewPi-script
    
            elif message_type == "resetWiFi":
                logMessage("Resetting controller WiFi settings")
                bg_ser.writeln("w")
                time.sleep(3)  # We'll give bg_ser 3 seconds for it to send/kick in
                sys.exit(0)  # Exit BrewPi-script
            else:
                logMessage("Error: Received invalid message on socket: " + message)
    
            if (time.time() - prev_time_out) < serial_check_interval:
                continue
            else:
                # raise exception to check serial for data immediately
                raise socket.timeout
    
        except socket.timeout:
            # Do serial communication and update settings every SerialCheckInterval
            prev_time_out = time.time()
    
            if hw_version is None:
                continue  # do nothing with the serial port when the controller has not been recognized
    
            if (time.time() - prev_lcd_update) > 5:
                # request new LCD text
                prev_lcd_update += 5  # give the controller some time to respond
                if hw_mode == "legacy":
                    # 'l' is only recognized on legacy controllers and results in an error for 'modern' controllers.
                    # We will need to emulate the LCD text
                    bg_ser.writeln('l')
    
            if (time.time() - prev_settings_update) > 60:
                # Request Settings from controller to stay up to date
                # Controller should send updates on changes, this is a periodic update to ensure it is up to date
                prev_settings_update += 5  # give the controller some time to respond
                bg_ser.writeln('s')
    
            # if no new data has been received for serialRequestInteval seconds
            if (time.time() - prev_data_time) >= float(config_obj.data_point_log_interval):
                if (time.time() - prev_time_out_req) > 5:  # It's been more than 5 seconds since we last requested temps
                    bg_ser.writeln("t")  # request new from controller
                    prev_time_out_req = time.time()
                    if prev_data_time == 0.0:  # If prevDataTime hasn't yet been set (it's 0.0 at startup), set it.
                        prev_data_time = time.time()
    
            if (time.time() - prev_data_time) >= 3 * float(config_obj.data_point_log_interval):
                # something is wrong: controller is not responding to data requests
                logMessage("Error: controller is not responding to new data requests. Exiting.")
    
                # In this case, we can rely on the process manager relaunching this script.
                # It's better to fail loudly (in this case with an exit) than silently.
                sys.exit(1)
    
            while True:
                line = bg_ser.read_line()
                message = bg_ser.read_message()
                if line is None and message is None:
                    break
                if line is not None:
                    try:
                        if line[0] == 'T':
                            # print it to stdout
                            if output_temperature:
                                print(time.strftime("%b %d %Y %H:%M:%S  ") + line[2:], flush=True)
    
                            # store time of last new data for interval check
                            prev_data_time = time.time()
    
                            # process temperature line
                            new_data = json.loads(line[2:])
                            # copy/rename keys
                            for key in new_data:
                                prev_temp_json[rename_temp_key(key)] = new_data[key]
    
                            new_row = prev_temp_json
    
                            # Moved this so that the last read values is updated even if logging is off. Otherwise, the
                            # getDashInfo will return the default temp values (0)
                            if config_obj.logging_status == config_obj.DATA_LOGGING_ACTIVE:
                                # All this is handled by the model
                                config_obj.save_beer_log_point(new_row)
    
                        elif line[0] == 'D':
                            # debug message received, should already been filtered out, but print anyway here.
                            logMessage("Finding a log message here should not be possible, report to the devs!")
                            logMessage("Line received was: {0}".format(line))
                        elif line[0] == 'L':
                            # lcd content received
                            prev_lcd_update = time.time()
                            lcd_text = json.loads(asciiToUnicode(line[2:]))
                        elif line[0] == 'C':
                            # Control constants received
                            cc = json.loads(line[2:])
                            sync_temp_format(control_constants=cc)  # Check the temp format just in case
                        elif line[0] == 'S':
                            # Control settings received
                            prev_settings_update = time.time()
                            cs = json.loads(line[2:])
                        # do not print this to the log file. This is requested continuously.
                        elif line[0] == 'V':
                            # Control settings received
                            cv = line[2:]  # keep as string, do not decode
                        elif line[0] == 'N':
                            pass  # version number received. Do nothing, just ignore
                        elif line[0] == 'h':
                            device_list['available'] = json.loads(line[2:])
                            old_list_state = device_list['listState']
                            device_list['listState'] = old_list_state.strip('h') + "h"
                            logMessage("Available devices received: " + json.dumps(device_list['available']))
                        elif line[0] == 'd':
                            device_list['installed'] = json.loads(line[2:])
                            old_list_state = device_list['listState']
                            device_list['listState'] = old_list_state.strip('d') + "d"
                            logMessage("Installed devices received: " + json.dumps(device_list['installed']))
                        elif line[0] == 'U':
                            logMessage("Device updated to: " + line[2:])
                        else:
                            logMessage("Cannot process line from controller: " + line)
                        # end or processing a line
                    except ValueError as e:
                        logMessage("JSON decode error: %s" % str(e))
                        logMessage("Line received was: " + line)
                    bg_ser.line_was_processed()  # Clean out the queue
                if message is not None:
                    try:
                        expanded_message = expandLogMessage.expandLogMessage(message)
                        logMessage("Controller debug message: " + expanded_message)
                    except Exception as e:  # catch all exceptions, because out of date file could cause errors
                        logMessage("Error while expanding log message '" + message + "'" + str(e))
                    bg_ser.message_was_processed()  # Clean out the queue
    
            # Check for update from temperature profile
            if 'mode' not in cs:
                logMessage("Error receiving mode from controller - restarting")
                sys.exit(1)
            if cs['mode'] == 'p':
                new_temp = config_obj.get_profile_temp()
    
                if new_temp is None:  # If we had an error loading a temperature (from dbConfig) disable temp control
                    cs['mode'] = 'o'
                    bg_ser.writeln("j{mode:\"o\"}")
                    logMessage("Notification: Error in profile mode - turning off temp control")
                    # raise socket.timeout  # go to serial communication to update controller
                elif round(new_temp, 2) != cs['beerSet']:
                    try:
                        new_temp = float(new_temp)
                        cs['beerSet'] = round(new_temp, 2)
                    except ValueError:
                        logMessage("Cannot convert temperature '" + new_temp + "' to float")
                        continue
                    # if temperature has to be updated send settings to controller
                    bg_ser.writeln("j{beerSet:" + json.dumps(cs['beerSet']) + "}")
    
                if config_obj.is_past_end_of_profile():
                    bg_ser.writeln("j{mode:\"b\", beerSet:" + json.dumps(cs['beerSet']) + "}")
                    cs['mode'] = 'b'
                    refresh_and_check(config_obj, run)  # Reload dbConfig from the database
                    config_obj.reset_profile()
                    logMessage("Notification: Beer temperature set to constant " + str(cs['beerSet']) +
                               " degrees at end of profile")
    
        except socket.error as e:
            logMessage("Socket error(%d): %s" % (e.errno, e.strerror))
            traceback.print_exc()
    
    if bg_ser:
        bg_ser.stop()
    
    if ser:
        if ser.isOpen():
            ser.close()  # close port
            
    if conn:
        conn.shutdown(socket.SHUT_RDWR)  # close socket
        conn.close()
