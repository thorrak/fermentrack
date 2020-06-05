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

from __future__ import print_function
import sys

sys.path.append("..")  # It's a hack, but it works. TODO - Fix this

from scriptlibs.BrewPiUtil import printStdErr, logMessage, asciiToUnicode

# Check needed software dependencies to nudge users to fix their setup
if sys.version_info < (3, 4):
    printStdErr("Sorry, requires Python 3.4.")
    sys.exit(1)

import time, socket, os, getopt, shutil, traceback
from django.core.exceptions import ObjectDoesNotExist


try:
    import urllib.parse as urllib
except:
    import urllib
from distutils.version import LooseVersion

import serial
from serial import SerialException
import json
import pid


#local imports
from scriptlibs import brewpiJson
import scriptlibs.BrewPiUtil as util
from scriptlibs import brewpiVersion
from scriptlibs import pinList
from scriptlibs import expandLogMessage
from scriptlibs.backgroundserial import BackGroundSerial


# For Fermentrack compatibility, try to load the Django includes. As this version is now Fermentrack only, die if this
# doesn't succeed.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# This is so Django knows where to find stuff.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fermentrack_django.settings")
sys.path.append(BASE_DIR)

# This is so my local_settings.py gets loaded.
os.chdir(BASE_DIR)

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
import app.models as models  # This SHOULD work due to the sys.path.append above.


# Settings will be read from controller, initialize with same defaults as controller
# This is mainly to show what's expected. Will all be overwritten on the first update from the controller

legacyHwVersion = "0.2.4"  # Minimum hardware version for 'legacy' branch support
developHwVersion = "0.4.0"  # Minimum hardware version for 'develop' branch support
compatibleHwVersion = legacyHwVersion  # Minimum supported version is 'legacy'
hwMode = ""  # Unused for now - either set to 'legacy' or '0.4.x'

# Control Settings
cs = dict(mode='b', beerSet=20.0, fridgeSet=20.0)

# Control Constants
cc = dict()

# Control variables (json string, sent directly to browser without decoding)
cv = "{}"

# listState = "", "d", "h", "dh" to reflect whether the list is up to date for installed (d) and available (h)
deviceList = dict(listState="", installed=[], available=[])

lcdText = ['Script starting up', ' ', ' ', ' ']

# Read in command line arguments
try:
    opts, args = getopt.getopt(sys.argv[1:], "hc:sqkfldwL",
                               ['help', 'config=', 'status', 'quit', 'kill', 'force', 'log', 'dontrunfile', 'checkstartuponly', 'dbcfg=', 'dblist', 'name=', 'pidfiledir='])
except getopt.GetoptError:
    printStdErr("Unknown parameter. Available options: --help, " +
        "--status, --quit, --kill, --force, --log, --dontrunfile, --dbcfg <Device name in database>, --dblist, " +
        "--name <name>, --pidfiledir <directory>")
    sys.exit()

# A BrewPiDevice object from Fermentrack (which contains all our configuration info)
dbConfig = None
device_id = None


def refresh_dbConfig() -> models.BrewPiDevice:
    global device_id

    if device_id is None:
        logMessage("No device ID was found - cannot load DB Config")
        exit(1)

    return models.BrewPiDevice.objects.get(id=device_id)


checkDontRunFile = False
checkStartupOnly = False
logToFiles = False

# Defaults
pidFileDir = "/tmp"

for o, a in opts:
    # print help message for command line options
    if o in ('-h', '--help'):
        printStdErr("\n Available command line options: ")
        printStdErr("--help: print this help message")
        printStdErr("--log: redirect stderr and stdout to log files")
        printStdErr("--dontrunfile: check dontrunfile in www directory and quit if it exists")
        printStdErr("--checkstartuponly: exit after startup checks, return 1 if startup is allowed")
        printStdErr("--dbcfg <Device ID in database>: loads configuration from database")
        printStdErr("--dblist: lists devices in the database")
        printStdErr("--pidfiledir <filename>: pid-file path/filename")
        exit()
    # supply a config file
    if o in ('--pidfiledir'):
        if not os.path.exists(a):
            sys.exit('ERROR: pidfiledir "%s" does not exist' % a)
        pidFileDir = a

    # list all devices in the database
    if o in ('-L', '--dblist'):
        try:
            dbDevices = models.BrewPiDevice.objects.all()
            print("=============== BrewPi Devices in Database ===============")
            if len(dbDevices) == 0:
                print("No configured devices found.")
            else:
                for d in dbDevices:
                    print("Devices:")
                    print("  %d: %s" % (d.id, d.device_name))
            print("===========================================================")
            exit()
        except Exception as e:
            sys.exit(e)

    # load the configuration from the database
    if o in ('-w', '--dbcfg'):

        # Try loading the database configuration from Django
        device_id = a
        try:
            dbConfig = refresh_dbConfig()
        except ObjectDoesNotExist:
            sys.exit('ERROR: No database configuration with the ID \'{}\' was found!'.format(a))


    # redirect output of stderr and stdout to files in log directory
    if o in ('-l', '--log'):
        logToFiles = True
    # only start brewpi when the dontrunfile is not found
    if o in ('-d', '--dontrunfile'):
        checkDontRunFile = True
    if o in ('--checkstartuponly'):
        checkStartupOnly = True


# Alright. We're modifying how we load the configuration file to allow for loading both from a database, and from the
# actual file-based config.

# If dbConfig wasn't set, we can't proceed (as we have no controller to manage)
if dbConfig is None:
    raise NotImplementedError('Only dbconfig installations are supported in this version of brewpi-script')

if dbConfig.status == models.BrewPiDevice.STATUS_ACTIVE or dbConfig.status == models.BrewPiDevice.STATUS_UNMANAGED:
    config = util.read_config_from_database_without_defaults(dbConfig)
else:
    logMessage("This instance of BrewPi is currently disabled in the web interface. Reenable it and relaunch "
               "this script. This instance will now exit.")
    exit(0)

# check for other running instances of BrewPi that will cause conflicts with this instance
pidFile = pid.PidFile(piddir=pidFileDir, pidname="brewpi-{}".format(device_id))
try:
    pidFile.create()
except pid.PidFileAlreadyLockedError:
    if not checkDontRunFile:  # Even for database configurations, we don't want to log this if the gatekeeper launched me
        logMessage("Another instance of BrewPi is already running, which will conflict with this instance. "
                   "This instance will exit")
    exit(0)
except pid.PidFileAlreadyRunningError:
    if not checkDontRunFile:  # Even for database configurations, we don't want to log this if the gatekeeper launched me
        logMessage("Another instance of BrewPi is already running, which will conflict with this instance. "
                   "This instance will exit")
    exit(0)


if checkStartupOnly:
    exit(1)

localJsonFileName = ""
localCsvFileName = ""
wwwJsonFileName = ""
wwwCsvFileName = ""
lastDay = ""
day = ""

if logToFiles:
    logPath = util.addSlash(util.scriptPath()) + 'logs/'
    logMessage("Redirecting output to log files in %s, output will not be shown in console" % logPath)
    sys.stderr = open(logPath + 'stderr.txt', 'a', 0)  # append to stderr file, unbuffered
    sys.stdout = open(logPath + 'stdout.txt', 'w', 0)  # overwrite stdout file on script start, unbuffered


def startNewBrew(newName):
    global config
    if len(newName) > 1:     # shorter names are probably invalid
        dbConfig = refresh_dbConfig()  # Reload dbConfig from the database
        config = util.configSet(dbConfig, 'beerName', newName)
        config = util.configSet(dbConfig, 'dataLogging', 'active')
        logMessage("Notification: Restarted logging for beer '%s'." % newName)
        return {'status': 0, 'statusMessage': "Successfully switched to new brew '%s'. " % urllib.unquote(newName) +
                                              "Please reload the page."}
    else:
        return {'status': 1, 'statusMessage': "Invalid new brew name '%s', "
                                              "please enter a name with at least 2 characters" % urllib.unquote(newName)}


def stopLogging():
    global config
    global dbConfig
    logMessage("Stopped data logging, as requested in web interface. " +
               "BrewPi will continue to control temperatures, but will not log any data.")
    dbConfig = refresh_dbConfig()  # Reload dbConfig from the database
    config = util.configSet(dbConfig, 'beerName', None)
    config = util.configSet(dbConfig, 'dataLogging', 'stopped')
    return {'status': 0, 'statusMessage': "Successfully stopped logging"}


def pauseLogging():
    global config
    global dbConfig
    logMessage("Paused logging data, as requested in web interface. " +
               "BrewPi will continue to control temperatures, but will not log any data until resumed.")
    if config['dataLogging'] == 'active':
        config = util.configSet(dbConfig, 'dataLogging', 'paused')
        dbConfig = refresh_dbConfig()  # Reload dbConfig from the database
        return {'status': 0, 'statusMessage': "Successfully paused logging."}
    else:
        return {'status': 1, 'statusMessage': "Logging already paused or stopped."}


def resumeLogging():
    global config
    global dbConfig
    logMessage("Continued logging data, as requested in web interface.")
    if config['dataLogging'] == 'paused':
        config = util.configSet(dbConfig, 'dataLogging', 'active')
        dbConfig = refresh_dbConfig()  # Reload dbConfig from the database
        return {'status': 0, 'statusMessage': "Successfully continued logging."}
    elif config['dataLogging'] == 'stopped':
        if dbConfig.active_beer is not None:
            config = util.configSet(dbConfig, 'dataLogging', 'active')
            dbConfig = refresh_dbConfig()  # Reload dbConfig from the database
            return {'status': 0, 'statusMessage': "Successfully continued logging."}
    # If we didn't return a success status above, we'll return an error
    return {'status': 1, 'statusMessage': "Logging was not resumed."}

# bytes are read from nonblocking serial into this buffer and processed when the buffer contains a full line.
ser = util.setupSerial(config, time_out=0)

if not ser:
    exit(1)

if len(urllib.unquote(config['beerName'])) > 1:
    logMessage("Notification: Script started for beer '" + urllib.unquote(config['beerName']) + "'")
else:
    logMessage("Notification: Script started, with no active beer being logged")

# wait for 10 seconds to allow an Uno to reboot (in case an Uno is being used)
time.sleep(float(config.get('startupDelay', 10)))


logMessage("Checking software version on controller... ")
hwVersion = brewpiVersion.getVersionFromSerial(ser)
if hwVersion is None:
    logMessage("Warning: Cannot receive version number from controller. " +
               "Your controller is either not programmed or running a very old version of BrewPi. " +
               "Please upload a new version of BrewPi to your controller.")
    # script will continue so you can at least program the controller
    lcdText = ['Could not receive', 'version from controller', 'Please (re)program', 'your controller']
    exit(1)
else:
    logMessage("Found " + hwVersion.toExtendedString() + " on port " + ser.name + "\n")
    if LooseVersion(hwVersion.toString()) < LooseVersion(compatibleHwVersion):
        # Completely incompatible. Unlikely to ever be triggered, as it requires pre-legacy code.
        logMessage("Warning: minimum BrewPi version compatible with this script is " +
                   compatibleHwVersion + " but version number received is " + hwVersion.toString() + ". Exiting.")
        exit(1)
    elif LooseVersion(hwVersion.toString()) < LooseVersion(legacyHwVersion):
        # Compatible, but only with pre-legacy (!) code. This should never happen as legacy support is the "oldest"
        # codebase we provide for.
        # This will generally never happen given that we are setting compatible = legacy above
        logMessage("Warning: minimum BrewPi version compatible with this script for legacy support is " +
                   legacyHwVersion + " but version number received is " + hwVersion.toString() + ". Exiting.")
        exit(1)
    elif LooseVersion(hwVersion.toString()) < LooseVersion(developHwVersion):
        # Version is between Legacy and 'develop' (v0.4.x) which means it receives 'legacy' support.
        # This MAY create issues with v0.3.x controllers - but I lack one to test.
        logMessage("BrewPi version received was {} which this script supports in ".format(hwVersion.toString()) +
                   "'legacy' branch mode.")
        hwMode = "legacy"
    else:
        logMessage("BrewPi version received was {} which this script supports in ".format(hwVersion.toString()) +
                   "'develop' branch mode.")
        hwMode = "modern"


    if int(hwVersion.log) != int(expandLogMessage.getVersion()):
        logMessage("Warning: version number of local copy of logMessages.h " +
                   "does not match log version number received from controller." +
                   "controller version = " + str(hwVersion.log) +
                   ", local copy version = " + str(expandLogMessage.getVersion()) +
                   ". This is generally a non-issue, as thus far log messages have only been added - not changed.")


bg_ser = None

if ser is not None:
    ser.flush()

    # set up background serial processing, which will continuously read data from serial and put whole lines in a queue
    bg_ser = BackGroundSerial(ser)
    bg_ser.start()
    # request settings from controller, processed later when reply is received
    bg_ser.writeln('s')  # request control settings cs
    bg_ser.writeln('c')  # request control constants cc
    bg_ser.writeln('v')  # request control variables cv

    # refresh the device list
    bg_ser.writeln("d{r:1}")        # request installed devices
    bg_ser.writeln("h{u:-1,v:1}")   # request available, but not installed devices

    # answer from controller is received asynchronously later.

# create a listening socket to communicate with PHP
is_windows = sys.platform.startswith('win')
useInetSocket = bool(config.get('useInetSocket', is_windows))
if useInetSocket:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    socketPort = config.get('socketPort', 6332)
    socketHost = config.get('socketHost', 'localhost')
    s.bind((socketHost, int(socketPort)))
    logMessage('Bound to TCP socket on port {}, interface {} '.format(int(socketPort), socketHost))
else:
    socketFile = util.addSlash(util.scriptPath()) + config.get('socket_name', 'BEERSOCKET')  # Making this configurable
    if os.path.exists(socketFile):
    # if socket already exists, remove it
        os.remove(socketFile)
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(socketFile)  # Bind BEERSOCKET
    # set all permissions for socket
    os.chmod(socketFile, 0o0777)

serialCheckInterval = 0.5
s.setblocking(1)  # set socket functions to be blocking
s.listen(10)  # Create a backlog queue for up to 10 connections
# blocking socket functions wait 'serialCheckInterval' seconds
s.settimeout(serialCheckInterval)


prevDataTime = 0.0  # keep track of time between new data requests
prevTimeOutReq = prevDataTime  # Using this to fix the prevDataTime tracking
prevTimeOut = time.time()
prevLcdUpdate = time.time()
prevSettingsUpdate = time.time()

run = 1

outputTemperature = True

prevTempJson = {
    "BeerTemp": 0,
    "FridgeTemp": 0,
    "BeerAnn": None,
    "FridgeAnn": None,
    "RoomTemp": None,
    "State": None,
    "BeerSet": 0,
    "FridgeSet": 0}

def renameTempKey(key):
    rename = {
        "Log1Temp": "RoomTemp", # Added for convenience, allows a configured OEM BrewPi to log room temp with Log1Temp
        "bt": "BeerTemp",
        "bs": "BeerSet",
        "ba": "BeerAnn",
        "ft": "FridgeTemp",
        "fs": "FridgeSet",
        "fa": "FridgeAnn",
        "rt": "RoomTemp",
        "s": "State",
        "t": "Time"}
    return rename.get(key, key)

# At startup, if we're using a db-based config, force synchronization of temperature format
def syncTempFormat(control_constants):
    db_temp_format = dbConfig.temp_format

    if control_constants['tempFormat'] != db_temp_format:
        # j{"tempFormat": "C"}
        settings_dict = {'tempFormat': dbConfig.temp_format}
        bg_ser.writeln("j" + json.dumps(settings_dict))
        # TODO - Set min/max temp if necessary


def trigger_refresh(read_values=False):
    # We want to keep the deviceList cache updated. Invalidate the cache, send a request to update the list to
    # the controller, then give it a few seconds to respond before raising socket.timeout & processing the
    # result.

    deviceList['listState'] = ""  # invalidate local copy
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
        conn.setblocking(1)
        # blocking receive, times out in serialCheckInterval
        message = conn.recv(4096)
        message = message.decode(encoding="cp437")
        if "=" in message:
            messageType, value = message.split("=", 1)
        else:
            messageType = message
            value = ""
        if messageType == "ack":  # acknowledge request
            conn.send(b'ack')
        elif messageType == "lcd":  # lcd contents requested
            if hwMode == "modern":
                # TODO - Emulate lcdText for modern controllers
                pass
            conn.send(json.dumps(lcdText).encode(encoding="cp437"))
        elif messageType == "getMode":  # echo cs['mode'] setting
            conn.send(cs['mode'].encode(encoding="cp437"))
        elif messageType == "getFridge":  # echo fridge temperature setting
            conn.send(json.dumps(cs['fridgeSet']).encode(encoding="cp437"))
        elif messageType == "getBeer":  # echo fridge temperature setting
            conn.send(json.dumps(cs['beerSet']).encode(encoding="cp437"))
        elif messageType == "getControlConstants":
            conn.send(json.dumps(cc).encode(encoding="cp437"))
        elif messageType == "getControlSettings":
            # TODO - See where/if we call getControlSettings (and fix the cs['profile'] response below)
            # if cs['mode'] == "p":
            #     profileFile = util.addSlash(util.scriptPath()) + 'settings/tempProfile.csv'
            #     with file(profileFile, 'r') as prof:
            #         cs['profile'] = prof.readline().split(",")[-1].rstrip("\n")
            cs['dataLogging'] = config['dataLogging']
            conn.send(json.dumps(cs).encode(encoding="cp437"))
        elif messageType == "getControlVariables":
            conn.send(cv.encode(encoding="cp437"))
        elif messageType == "refreshControlConstants":
            bg_ser.writeln("c")
            raise socket.timeout
        elif messageType == "refreshControlSettings":
            bg_ser.writeln("s")
            raise socket.timeout
        elif messageType == "refreshControlVariables":
            bg_ser.writeln("v")
            raise socket.timeout
        elif messageType == "loadDefaultControlSettings":
            bg_ser.writeln("S")
            raise socket.timeout
        elif messageType == "loadDefaultControlConstants":
            bg_ser.writeln("C")
            raise socket.timeout
        elif messageType == "setBeer":  # new constant beer temperature received
            try:
                newTemp = float(value)
                cs['beerSet'] = round(newTemp, 2)
            except ValueError:
                logMessage("Cannot convert temperature '" + value + "' to float")
                continue

            cs['mode'] = 'b'
            # round to 2 dec, python will otherwise produce 6.999999999
            bg_ser.writeln("j{{mode:b, beerSet:{}}}".format(cs['beerSet']))
            dbConfig = refresh_dbConfig()  # Reload dbConfig from the database (in case we were using profiles)
            logMessage("Notification: Beer temperature set to {} degrees in web interface".format(cs['beerSet']))
            raise socket.timeout  # go to serial communication to update controller

        elif messageType == "setFridge":  # new constant fridge temperature received
            try:
                newTemp = float(value)
            except ValueError:
                logMessage("Cannot convert temperature '" + value + "' to float")
                continue

            cs['mode'] = 'f'
            cs['fridgeSet'] = round(newTemp, 2)
            bg_ser.writeln("j{mode:f, fridgeSet:" + json.dumps(cs['fridgeSet']) + "}")
            # Reload dbConfig from the database (in case we were using profiles)
            dbConfig = refresh_dbConfig()  # Reload dbConfig from the database
            logMessage("Notification: Fridge temperature set to " +
                       str(cs['fridgeSet']) +
                       " degrees in web interface")
            raise socket.timeout  # go to serial communication to update controller

        elif messageType == "setOff":  # cs['mode'] set to OFF
            cs['mode'] = 'o'
            bg_ser.writeln("j{mode:o}")
            dbConfig = refresh_dbConfig()   # Reload dbConfig from the database (in case we were using profiles)
            logMessage("Notification: Temperature control disabled")
            raise socket.timeout
        elif messageType == "setParameters":
            # receive JSON key:value pairs to set parameters on the controller
            try:
                decoded = json.loads(value)
                bg_ser.writeln("j" + json.dumps(decoded))
                if 'tempFormat' in decoded:
                    if decoded['tempFormat'] != config.get('temp_format', 'C'):
                        # For database configured installs, we save this in the device definition
                        util.configSet(dbConfig, 'temp_format', decoded['tempFormat'])
                    dbConfig = refresh_dbConfig()  # Reload dbConfig from the database
            except ValueError:
                logMessage("Error: invalid JSON parameter string received: " + value)
            raise socket.timeout
        elif messageType == "stopScript":  # exit instruction received. Stop script.
            # voluntary shutdown.
            log_message = "stopScript message received on socket. "
            run = 0
            log_message += "dbConfig in use - assuming device status was already properly updated "
            log_message += "to prevent automatic restart"
            logMessage(log_message)
            continue
        elif messageType == "quit":  # quit instruction received. Probably sent by another brewpi script instance
            logMessage("quit message received on socket. Stopping script.")
            run = 0
            # Leave dontrunfile alone.
            # This instruction is meant to restart the script or replace it with another instance.
            continue
        elif messageType == "eraseLogs":
            logMessage('eraseLogs is not implemented for this version of brewpi-script')
        elif messageType == "interval":  # new interval received
            newInterval = int(value)
            if 5 < newInterval < 5000:
                try:
                    config = util.configSet(dbConfig, 'interval', float(newInterval))
                except ValueError:
                    logMessage("Cannot convert interval '" + value + "' to float")
                    continue
                logMessage("Notification: Interval changed to " + str(newInterval) + " seconds")
        elif messageType == "startNewBrew":  # new beer name
            newName = value
            result = startNewBrew(newName)
            conn.send(json.dumps(result).encode(encoding="cp437"))
        elif messageType == "pauseLogging":
            result = pauseLogging()
            conn.send(json.dumps(result).encode(encoding="cp437"))
        elif messageType == "stopLogging":
            result = stopLogging()
            conn.send(json.dumps(result).encode(encoding="cp437"))
        elif messageType == "resumeLogging":
            result = resumeLogging()
            conn.send(json.dumps(result).encode(encoding="cp437"))
        elif messageType == "dateTimeFormatDisplay":
            logMessage('dateTimeFormatDisplay is not implemetned for this version of brewpi-script')
        elif messageType == "setActiveProfile":
            # We're using a dbConfig object to manage everything. We aren't being passed anything by Fermentrack
            logMessage("Setting controller to beer profile mode using database-configured profile")
            conn.send(b"Profile successfully updated")
            dbConfig = refresh_dbConfig()  # Reload dbConfig from the database
            if cs['mode'] is not 'p':
                cs['mode'] = 'p'
                bg_ser.writeln("j{mode:p}")
                logMessage("Notification: Profile mode enabled")
                raise socket.timeout  # go to serial communication to update controller

        elif messageType == "programController" or messageType == "programArduino":
            logMessage("programController action is not supported by this modified version of brewpi-script")
        elif messageType == "refreshDeviceList":
            # if value.find("readValues") != -1:
                trigger_refresh(True)
            # else:
            #     trigger_refresh(False)
        elif messageType == "getDeviceList":
            if deviceList['listState'] in ["dh", "hd"]:
                response = dict(board=hwVersion.board,
                                shield=hwVersion.shield,
                                deviceList=deviceList,
                                pinList=pinList.getPinList(hwVersion.board, hwVersion.shield))
                conn.send(json.dumps(response).encode(encoding="cp437"))
            else:
                # It's up to the web interface to track how often it requests an update
                conn.send(b"device-list-not-up-to-date")
                raise socket.timeout
        elif messageType == "getDashInfo":
            # This is a new messageType
            response = {"BeerTemp": prevTempJson['BeerTemp'],
                        "FridgeTemp": prevTempJson['FridgeTemp'],
                        "BeerAnn": prevTempJson['BeerAnn'],
                        "FridgeAnn": prevTempJson['FridgeAnn'],
                        "RoomTemp": prevTempJson['RoomTemp'],
                        "State": prevTempJson['State'],
                        "BeerSet": prevTempJson['BeerSet'],
                        "FridgeSet": prevTempJson['FridgeSet'],
                        "LogInterval": config['interval'],
                        "Mode": cs['mode']}
            conn.send(json.dumps(response).encode(encoding="cp437"))
        elif messageType == "applyDevice":
            # applyDevice is used to apply settings to an existing device (pin/OneWire assignment, etc.)
            try:
                configStringJson = json.loads(value)  # load as JSON to check syntax
            except ValueError:
                logMessage("Error: invalid JSON parameter string received: " + value)
                continue
            logMessage("Received applyDevice request, updating to: {}".format(value))
            # bg_ser.writeln("U" + json.dumps(configStringJson))
            # No need to reencode to JSON if we received valid JSON in the first place.
            bg_ser.writeln("U" + value)

            trigger_refresh(True)
        elif messageType == "writeDevice":
            # writeDevice is used to -create- "actuators" -- Specifically, (for now) buttons.
            try:
                configStringJson = json.loads(value)  # load as JSON to check syntax
            except ValueError:
                logMessage("Error: invalid JSON parameter string received: " + value)
                continue
            bg_ser.writeln("d" + json.dumps(configStringJson))

            # We want to keep the deviceList cache updated. Invalidate the cache, send a request to update the list to
            # the controller, then give it a few seconds to respond before raising socket.timeout & processing the
            # result.
            trigger_refresh(True)
        elif messageType == "getVersion":
            if hwVersion:
                response = hwVersion.__dict__
                # replace LooseVersion with string, because it is not JSON serializable
                response['version'] = hwVersion.toString()
            else:
                response = {}
            response_str = json.dumps(response)
            conn.send(response_str.encode(encoding="cp437"))

        elif messageType == "resetController":
            logMessage("Resetting controller to factory defaults")
            bg_ser.writeln("E")
            # request settings from controller, processed later when reply is received
            bg_ser.writeln('s')  # request control settings cs
            bg_ser.writeln('c')  # request control constants cc
            bg_ser.writeln('v')  # request control variables cv
            trigger_refresh(True)  # Refresh the device list cache (will also raise socket.timeout)

        elif messageType == "restartController":
            logMessage("Restarting controller")
            bg_ser.writeln("R")  # This tells the controller to restart
            time.sleep(3)        # We'll give bg_ser 3 seconds for it to send/kick in
            sys.exit(0)          # Exit BrewPi-script

        elif messageType == "resetWiFi":
            logMessage("Resetting controller WiFi settings")
            bg_ser.writeln("w")
            # TODO - Determine if we should sleep & exit here
            trigger_refresh(True)  # Refresh the device list cache (will also raise socket.timeout)

        else:
            logMessage("Error: Received invalid message on socket: " + message)

        if (time.time() - prevTimeOut) < serialCheckInterval:
            continue
        else:
            # raise exception to check serial for data immediately
            raise socket.timeout

    except socket.timeout:
        # Do serial communication and update settings every SerialCheckInterval
        prevTimeOut = time.time()

        if hwVersion is None:
            continue  # do nothing with the serial port when the controller has not been recognized

        if(time.time() - prevLcdUpdate) > 5:
            # request new LCD text
            prevLcdUpdate += 5 # give the controller some time to respond
            if hwMode == "legacy":
                # 'l' is only recognized on legacy controllers and results in an error for 'modern' controllers.
                # We will need to emulate the LCD text
                bg_ser.writeln('l')

        if(time.time() - prevSettingsUpdate) > 60:
            # Request Settings from controller to stay up to date
            # Controller should send updates on changes, this is a periodic update to ensure it is up to date
            prevSettingsUpdate += 5 # give the controller some time to respond
            bg_ser.writeln('s')

        # if no new data has been received for serialRequestInteval seconds
        if (time.time() - prevDataTime) >= float(config['interval']):
            if (time.time() - prevTimeOutReq) > 5:  # If it's been more than 5 seconds since we last requested temps
                bg_ser.writeln("t")  # request new from controller
                prevTimeOutReq = time.time()
                if prevDataTime == 0.0:  # If prevDataTime hasn't yet been set (it's 0.0 at script startup), set it.
                    prevDataTime = time.time()

        if (time.time() - prevDataTime) >= 3 * float(config['interval']):
            # something is wrong: controller is not responding to data requests
            logMessage("Error: controller is not responding to new data requests. Exiting.")

            # In this case, we can rely on either circus (Fermentrack) or cron (brewpi-www) relaunching this script.
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
                        if outputTemperature:
                            print(time.strftime("%b %d %Y %H:%M:%S  ") + line[2:])

                        # store time of last new data for interval check
                        prevDataTime = time.time()

                        if config['dataLogging'] == 'paused' or config['dataLogging'] == 'stopped':
                            continue  # skip if logging is paused or stopped

                        # process temperature line
                        newData = json.loads(line[2:])
                        # copy/rename keys
                        for key in newData:
                            prevTempJson[renameTempKey(key)] = newData[key]

                        newRow = prevTempJson

                        # All this is handled by the model
                        util.save_beer_log_point(dbConfig, newRow)

                    elif line[0] == 'D':
                        # debug message received, should already been filtered out, but print anyway here.
                        logMessage("Finding a log message here should not be possible, report to the devs!")
                        logMessage("Line received was: {0}".format(line))
                    elif line[0] == 'L':
                        # lcd content received
                        prevLcdUpdate = time.time()
                        lcdText = json.loads(asciiToUnicode(line[2:]))
                    elif line[0] == 'C':
                        # Control constants received
                        cc = json.loads(line[2:])
                        syncTempFormat(control_constants=cc)  # Check the temp format just in case
                    elif line[0] == 'S':
                        # Control settings received
                        prevSettingsUpdate = time.time()
                        cs = json.loads(line[2:])
                    # do not print this to the log file. This is requested continuously.
                    elif line[0] == 'V':
                        # Control settings received
                        cv = line[2:] # keep as string, do not decode
                    elif line[0] == 'N':
                        pass  # version number received. Do nothing, just ignore
                    elif line[0] == 'h':
                        deviceList['available'] = json.loads(line[2:])
                        oldListState = deviceList['listState']
                        deviceList['listState'] = oldListState.strip('h') + "h"
                        logMessage("Available devices received: "+ json.dumps(deviceList['available']))
                    elif line[0] == 'd':
                        deviceList['installed'] = json.loads(line[2:])
                        oldListState = deviceList['listState']
                        deviceList['listState'] = oldListState.strip('d') + "d"
                        logMessage("Installed devices received: " + json.dumps(deviceList['installed']))
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
                    expandedMessage = expandLogMessage.expandLogMessage(message)
                    logMessage("Controller debug message: " + expandedMessage)
                except Exception as e:  # catch all exceptions, because out of date file could cause errors
                    logMessage("Error while expanding log message '" + message + "'" + str(e))
                bg_ser.message_was_processed()  # Clean out the queue

        # Check for update from temperature profile
        if 'mode' not in cs:
            logMessage("Error receiving mode from controller - restarting")
            sys.exit(1)
        if cs['mode'] == 'p':
            newTemp = dbConfig.get_profile_temp()  # Use the Django model

            if newTemp is None:  # If we had an error loading a temperature (from dbConfig) disable temp control
                cs['mode'] = 'o'
                bg_ser.writeln("j{mode:o}")
                logMessage("Notification: Error in profile mode - turning off temp control")
                # raise socket.timeout  # go to serial communication to update controller
            elif newTemp != cs['beerSet']:
                try:
                    newTemp = float(newTemp)
                    cs['beerSet'] = round(newTemp, 2)
                except ValueError:
                    logMessage("Cannot convert temperature '" + newTemp + "' to float")
                    continue
                # if temperature has to be updated send settings to controller
                bg_ser.writeln("j{beerSet:" + json.dumps(cs['beerSet']) + "}")

            if dbConfig.is_past_end_of_profile():
                bg_ser.writeln("j{mode:b, beerSet:" + json.dumps(cs['beerSet']) + "}")
                cs['mode'] = 'b'
                dbConfig = refresh_dbConfig()  # Reload dbConfig from the database
                dbConfig.reset_profile()
                logMessage("Notification: Beer temperature set to constant " + str(cs['beerSet']) +
                           " degrees at end of profile")

    except (socket.error) as e:
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
