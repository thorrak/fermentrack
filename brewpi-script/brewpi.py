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
import os, sys

# Load up the Django specific stuff
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# This is so Django knows where to find stuff.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "brewpi_django.settings")
sys.path.append(BASE_DIR)

# This is so my local_settings.py gets loaded.
os.chdir(BASE_DIR)

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

import app.models as models  # This SHOULD work due to the sys.path.append above.


from BrewPiUtil import printStdErr
from BrewPiUtil import logMessage

# Check needed software dependencies to nudge users to fix their setup
if sys.version_info < (2, 7):
    printStdErr("Sorry, requires Python 2.7.")
    sys.exit(1)

# standard libraries
import time
import socket
import os
import getopt
from pprint import pprint
import shutil
import traceback
import urllib
from distutils.version import LooseVersion
from serial import SerialException

# load non standard packages, exit when they are not installed
try:
    import serial
    if LooseVersion(serial.VERSION) < LooseVersion("3.0"):
        printStdErr("BrewPi requires pyserial 3.0, you have version {0} installed.\n".format(serial.VERSION) +
                             "Please upgrade pyserial via pip, by running:\n" +
                             "  sudo pip install pyserial --upgrade\n" +
                             "If you do not have pip installed, install it with:\n" +
                             "  sudo apt-get install build-essential python-dev python-pip\n")
        sys.exit(1)
except ImportError:
    printStdErr("BrewPi requires PySerial to run, please install it via pip, by running:\n" +
                             "  sudo pip install pyserial --upgrade\n" +
                             "If you do not have pip installed, install it with:\n" +
                             "  sudo apt-get install build-essential python-dev python-pip\n")
    sys.exit(1)
try:
    import simplejson as json
except ImportError:
    printStdErr("BrewPi requires simplejson to run, please install it with 'sudo apt-get install python-simplejson")
    sys.exit(1)
try:
    from configobj import ConfigObj
except ImportError:
    printStdErr("BrewPi requires ConfigObj to run, please install it with 'sudo apt-get install python-configobj")
    sys.exit(1)


#local imports
import temperatureProfile
import programController as programmer
import brewpiJson
import BrewPiUtil as util
import brewpiVersion
import pinList
import expandLogMessage
import BrewPiProcess
from backgroundserial import BackGroundSerial


# Settings will be read from controller, initialize with same defaults as controller
# This is mainly to show what's expected. Will all be overwritten on the first update from the controller

compatibleHwVersion = "0.4.0"

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
    opts, args = getopt.getopt(sys.argv[1:], "hc:sqkfldwt",
                               ['help', 'config=', 'status', 'quit', 'kill', 'force', 'log', 'dontrunfile', 'checkstartuponly', 'dbcfg=', 'templog='])
except getopt.GetoptError:
    printStdErr("Unknown parameter, available Options: --help, --config <path to config file>, " +
        "--status, --quit, --kill, --force, --log, --dontrunfile, --dbcfg <Device name in database>, " +
        "--templog <flatfile|db|both>")
    sys.exit()

configFile = None
checkDontRunFile = False
checkStartupOnly = False
logToFiles = False
tempLogType = "flatfile"  # This is the default (existing) log type. Logs to flat files (json/csv)
dbConfig = None  # The object containing the database configuration

for o, a in opts:
    # print help message for command line options
    if o in ('-h', '--help'):
        printStdErr("\n Available command line options: ")
        printStdErr("--help: print this help message")
        printStdErr("--config <path to config file>: specify a config file to use. When omitted settings/config.cf is used. Not compatible with dbcfg.")
        printStdErr("--status: check which scripts are already running")
        printStdErr("--quit: ask all  instances of BrewPi to quit by sending a message to their socket")
        printStdErr("--kill: kill all instances of BrewPi by sending SIGKILL")
        printStdErr("--force: Force quit/kill conflicting instances of BrewPi and keep this one")
        printStdErr("--log: redirect stderr and stdout to log files")
        printStdErr("--dontrunfile: check dontrunfile in www directory and quit if it exists")
        printStdErr("--checkstartuponly: exit after startup checks, return 1 if startup is allowed")
        printStdErr("--dbcfg <Device name in database>: loads configuration from database")
        printStdErr("--templog <flatfile|db|both>: log temperature data to flatfile (default), database, or both")
        exit()
    # supply a config file
    if o in ('-c', '--config'):
        configFile = os.path.abspath(a)
        if not os.path.exists(configFile):
            sys.exit('ERROR: Config file "%s" was not found!' % configFile)
        if dbConfig:
            sys.exit('ERROR: Cannot use both --config and --dbcfg! Pick one and try again!')

    # load the configuration from the database
    if o in ('-w', '--dbcfg'):
        # Try loading the database configuration from
        try:
            dbConfig = models.BrewPiDevice.objects.get(device_name=a)
        except:
            sys.exit('ERROR: No database configuration with the name \'{}\' was found!'.format(a))
        if configFile:
            sys.exit('ERROR: Cannot use both --config and --dbcfg! Pick one and try again!')

    # send quit instruction to all running instances of BrewPi
    if o in ('-s', '--status'):
        allProcesses = BrewPiProcess.BrewPiProcesses()
        allProcesses.update()
        running = allProcesses.as_dict()
        if running:
            pprint(running)
        else:
            printStdErr("No BrewPi scripts running")
        exit()
    # quit/kill running instances, then keep this one
    if o in ('-q', '--quit'):
        logMessage("Asking all BrewPi Processes to quit on their socket")
        allProcesses = BrewPiProcess.BrewPiProcesses()
        allProcesses.quitAll()
        time.sleep(2)
        exit()
    # send SIGKILL to all running instances of BrewPi
    if o in ('-k', '--kill'):
        logMessage("Killing all BrewPi Processes")
        allProcesses = BrewPiProcess.BrewPiProcesses()
        allProcesses.killAll()
        exit()
    # close all existing instances of BrewPi by quit/kill and keep this one
    if o in ('-f', '--force'):
        logMessage("Closing all existing processes of BrewPi and keeping this one")
        allProcesses = BrewPiProcess.BrewPiProcesses()
        if len(allProcesses.update()) > 1:  # if I am not the only one running
            allProcesses.quitAll()
            time.sleep(2)
            if len(allProcesses.update()) > 1:
                printStdErr("Asking the other processes to quit nicely did not work. Killing them with force!")
    # redirect output of stderr and stdout to files in log directory
    if o in ('-l', '--log'):
        logToFiles = True
    # only start brewpi when the dontrunfile is not found
    if o in ('-d', '--dontrunfile'):
        checkDontRunFile = True
    if o in ('--checkstartuponly'):
        checkStartupOnly = True
    # If we want to log to a database rather than flat files, specify as such
    if o in ('-t', '--templog'):
        if a <> "flatfile" and a <> "db" and a <> "both":
            sys.exit('ERROR: --templog must be \'flatfile\', \'db\', or \'both\'. \'{}\' is an invalid choice.'.format(a))
        tempLogType = a


# Alright. We're modifying how we load the configuration file to allow for loading both from a database, and from the
# actual file-based config.

# If neither configFile or dbConfig were set, assume we need to load defaults
if not configFile and not dbConfig:
    configFile = util.addSlash(sys.path[0]) + 'settings/config.cfg'

if configFile:  # If we had a file-based config (or are defaulting) then load the config file
    config = util.read_config_file_with_defaults(configFile)

    # check dont run file when it exists and exit it it does
    # Doing this here, because we explicitly save the process ID for database configurations
    if checkDontRunFile:
        dontRunFilePath = os.path.join(config['wwwPath'], 'do_not_run_brewpi')
        if os.path.exists(dontRunFilePath):
            # do not print anything, this will flood the logs
            exit(0)
    if tempLogType <> "flatfile":
        sys.exit('ERROR: When saving datapoints to the database, --dbcfg must be used!')
elif dbConfig:  # Load from the database
    # TODO - Make sure the process ID check below works
    config = util.read_config_from_database_without_defaults(dbConfig)
else:  # This should never be hit - Just adding it to the code to make it clear that if neither of these work, we exit
    exit(1)


# check for other running instances of BrewPi that will cause conflicts with this instance
allProcesses = BrewPiProcess.BrewPiProcesses()
allProcesses.update()
myProcess = allProcesses.me()
if allProcesses.findConflicts(myProcess):
    if not checkDontRunFile:  # Even for database configurations, we don't want to log this if the gatekeeper launched me
        logMessage("Another instance of BrewPi is already running, which will conflict with this instance. " +
                   "This instance will exit")
    exit(0)
elif dbConfig:
    # If there is no conflict, save the process ID
    config = util.configSet(configFile, dbConfig, 'process_id', os.getpid())

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


# userSettings.json is a copy of some of the settings that are needed by the web server.
# This allows the web server to load properly, even when the script is not running.
def changeWwwSetting(settingName, value):
    if config.get('use_brewpi_www', True):  # If we don't have a PHP-based brewpi-www installed, we don't use this code
        wwwSettingsFileName = util.addSlash(config['wwwPath']) + 'userSettings.json'
        if os.path.exists(wwwSettingsFileName):
            wwwSettingsFile = open(wwwSettingsFileName, 'r+b')
            try:
                wwwSettings = json.load(wwwSettingsFile)  # read existing settings
            except json.JSONDecodeError:
                logMessage("Error in decoding userSettings.json, creating new empty json file")
                wwwSettings = {}  # start with a fresh file when the json is corrupt.
        else:
            wwwSettingsFile = open(wwwSettingsFileName, 'w+b')  # create new file
            wwwSettings = {}

        wwwSettings[settingName] = str(value)
        wwwSettingsFile.seek(0)
        wwwSettingsFile.write(json.dumps(wwwSettings))
        wwwSettingsFile.truncate()
        wwwSettingsFile.close()


def setFiles():
    global config
    global localJsonFileName
    global localCsvFileName
    global wwwJsonFileName
    global wwwCsvFileName
    global lastDay
    global day

    if tempLogType == "flatfile" or tempLogType == "both":

        # create directory for the data if it does not exist
        beerFileName = config['beerName']
        dataPath = util.addSlash(util.addSlash(util.scriptPath()) + 'data/' + beerFileName)
        wwwDataPath = util.addSlash(util.addSlash(config['wwwPath']) + 'data/' + beerFileName)

        if not os.path.exists(dataPath):
            os.makedirs(dataPath)
            os.chmod(dataPath, 0775)  # give group all permissions
        if not os.path.exists(wwwDataPath):
            os.makedirs(wwwDataPath)
            os.chmod(wwwDataPath, 0775)  # give group all permissions

        # Keep track of day and make new data file for each day
        day = time.strftime("%Y-%m-%d")
        lastDay = day
        # define a JSON file to store the data
        jsonFileName = beerFileName + '-' + day

        #if a file for today already existed, add suffix
        if os.path.isfile(dataPath + jsonFileName + '.json'):
            i = 1
            while os.path.isfile(dataPath + jsonFileName + '-' + str(i) + '.json'):
                i += 1
            jsonFileName = jsonFileName + '-' + str(i)

        localJsonFileName = dataPath + jsonFileName + '.json'
        brewpiJson.newEmptyFile(localJsonFileName)

        # Define a location on the web server to copy the file to after it is written
        wwwJsonFileName = wwwDataPath + jsonFileName + '.json'

        # Define a CSV file to store the data as CSV (might be useful one day)
        localCsvFileName = (dataPath + beerFileName + '.csv')
        wwwCsvFileName = (wwwDataPath + beerFileName + '.csv')

        # create new empty json file
        brewpiJson.newEmptyFile(localJsonFileName)

def startBeer(beerName):
    if tempLogType == "flatfile" or tempLogType == "both":
        if config['dataLogging'] == 'active':
            setFiles()
        changeWwwSetting('beerName', beerName)

    # If we're saving to the database, we need to create the beer (possibly) and link it to the chamber
    if (tempLogType == "db" or tempLogType == "both") and beerName <> "":
        new_beer, created = models.Beer.objects.get_or_create(name=beerName, device=dbConfig)
        dbConfig.active_beer = new_beer


def startNewBrew(newName):
    global config
    if len(newName) > 1:     # shorter names are probably invalid
        config = util.configSet(configFile, dbConfig, 'beerName', newName)
        config = util.configSet(configFile, dbConfig, 'dataLogging', 'active')
        startBeer(newName)
        logMessage("Notification: Restarted logging for beer '%s'." % newName)
        return {'status': 0, 'statusMessage': "Successfully switched to new brew '%s'. " % urllib.unquote(newName) +
                                              "Please reload the page."}
    else:
        return {'status': 1, 'statusMessage': "Invalid new brew name '%s', "
                                              "please enter a name with at least 2 characters" % urllib.unquote(newName)}


def stopLogging():
    global config
    logMessage("Stopped data logging, as requested in web interface. " +
               "BrewPi will continue to control temperatures, but will not log any data.")
    config = util.configSet(configFile, dbConfig, 'beerName', None)  # TODO - Edit this line to work with the database
    config = util.configSet(configFile, dbConfig, 'dataLogging', 'stopped')
    changeWwwSetting('beerName', None)
    return {'status': 0, 'statusMessage': "Successfully stopped logging"}


def pauseLogging():
    global config
    logMessage("Paused logging data, as requested in web interface. " +
               "BrewPi will continue to control temperatures, but will not log any data until resumed.")
    if config['dataLogging'] == 'active':
        config = util.configSet(configFile, dbConfig, 'dataLogging', 'paused')
        return {'status': 0, 'statusMessage': "Successfully paused logging."}
    else:
        return {'status': 1, 'statusMessage': "Logging already paused or stopped."}


def resumeLogging():
    global config
    logMessage("Continued logging data, as requested in web interface.")
    if config['dataLogging'] == 'paused':
        config = util.configSet(configFile, dbConfig, 'dataLogging', 'active')
        return {'status': 0, 'statusMessage': "Successfully continued logging."}
    else:
        return {'status': 1, 'statusMessage': "Logging was not paused."}

# bytes are read from nonblocking serial into this buffer and processed when the buffer contains a full line.
ser = util.setupSerial(config, time_out=0)

if not ser:
    exit(1)

logMessage("Notification: Script started for beer '" + urllib.unquote(config['beerName']) + "'")
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
else:
    logMessage("Found " + hwVersion.toExtendedString() + \
               " on port " + ser.name + "\n")
    if LooseVersion( hwVersion.toString() ) < LooseVersion(compatibleHwVersion):
        logMessage("Warning: minimum BrewPi version compatible with this script is " +
                   compatibleHwVersion +
                   " but version number received is " + hwVersion.toString())
    if int(hwVersion.log) != int(expandLogMessage.getVersion()):
        logMessage("Warning: version number of local copy of logMessages.h " +
                   "does not match log version number received from controller." +
                   "controller version = " + str(hwVersion.log) +
                   ", local copy version = " + str(expandLogMessage.getVersion()))
    if hwVersion.family == 'Arduino':  # TODO - Determine if there is really any reason for this (and remove if not)
        exit("\n ERROR: the newest version of BrewPi is not compatible with Arduino. \n" +
            "You can use our legacy branch with your Arduino, in which we only include the backwards compatible changes. \n" +
            "To change to the legacy branch, run: sudo ~/brewpi-tools/updater.py --ask , and choose the legacy branch.")


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
    os.chmod(socketFile, 0777)

serialCheckInterval = 0.5
s.setblocking(1)  # set socket functions to be blocking
s.listen(10)  # Create a backlog queue for up to 10 connections
# blocking socket functions wait 'serialCheckInterval' seconds
s.settimeout(serialCheckInterval)


prevDataTime = 0.0  # keep track of time between new data requests
prevTimeOut = time.time()
prevLcdUpdate = time.time()
prevSettingsUpdate = time.time()

run = 1

startBeer(config['beerName'])
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

while run:
    if config['dataLogging'] == 'active':
        # Check whether it is a new day
        if tempLogType == "flatfile" or tempLogType == "both":
            # We only need to do the day role if we're saving to flatfiles
            lastDay = day
            day = time.strftime("%Y-%m-%d")
            if lastDay != day:
                logMessage("Notification: New day, creating new JSON file.")
                setFiles()

    # Wait for incoming socket connections.
    # When nothing is received, socket.timeout will be raised after
    # serialCheckInterval seconds. Serial receive will be done then.
    # When messages are expected on serial, the timeout is raised 'manually'
    try:
        conn, addr = s.accept()
        conn.setblocking(1)
        # blocking receive, times out in serialCheckInterval
        message = conn.recv(4096)
        if "=" in message:
            messageType, value = message.split("=", 1)
        else:
            messageType = message
            value = ""
        if messageType == "ack":  # acknowledge request
            conn.send('ack')
        elif messageType == "lcd":  # lcd contents requested
            conn.send(json.dumps(lcdText))
        elif messageType == "getMode":  # echo cs['mode'] setting
            conn.send(cs['mode'])
        elif messageType == "getFridge":  # echo fridge temperature setting
            conn.send(json.dumps(cs['fridgeSet']))
        elif messageType == "getBeer":  # echo fridge temperature setting
            conn.send(json.dumps(cs['beerSet']))
        elif messageType == "getControlConstants":
            conn.send(json.dumps(cc))
        elif messageType == "getControlSettings":
            if cs['mode'] == "p":
                profileFile = util.addSlash(util.scriptPath()) + 'settings/tempProfile.csv'
                with file(profileFile, 'r') as prof:
                    cs['profile'] = prof.readline().split(",")[-1].rstrip("\n")
            cs['dataLogging'] = config['dataLogging']
            conn.send(json.dumps(cs))
        elif messageType == "getControlVariables":
            conn.send(cv)
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
            except ValueError:
                logMessage("Cannot convert temperature '" + value + "' to float")
                continue

            cs['mode'] = 'b'
            # round to 2 dec, python will otherwise produce 6.999999999
            cs['beerSet'] = round(newTemp, 2)
            bg_ser.writeln("j{mode:b, beerSet:" + json.dumps(cs['beerSet']) + "}")
            logMessage("Notification: Beer temperature set to " +
                       str(cs['beerSet']) +
                       " degrees in web interface")
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
            logMessage("Notification: Fridge temperature set to " +
                       str(cs['fridgeSet']) +
                       " degrees in web interface")
            raise socket.timeout  # go to serial communication to update controller

        elif messageType == "setOff":  # cs['mode'] set to OFF
            cs['mode'] = 'o'
            bg_ser.writeln("j{mode:o}")
            logMessage("Notification: Temperature control disabled")
            raise socket.timeout
        elif messageType == "setParameters":
            # receive JSON key:value pairs to set parameters on the controller
            try:
                decoded = json.loads(value)
                bg_ser.writeln("j" + json.dumps(decoded))
                if 'tempFormat' in decoded:
                    changeWwwSetting('tempFormat', decoded['tempFormat'])  # change in web interface settings too.
                    if decoded['tempFormat'] <> config.get('temp_format', 'C') and dbConfig:
                        # For database configured installs, we save this in the device definition
                        util.configSet(configFile, dbConfig, 'temp_format', decoded['tempFormat'])
            except json.JSONDecodeError:
                logMessage("Error: invalid JSON parameter string received: " + value)
            raise socket.timeout
        elif messageType == "stopScript":  # exit instruction received. Stop script.
            # voluntary shutdown.
            # write a file to prevent the cron job from restarting the script
            logMessage("stopScript message received on socket. " +
                       "Stopping script and writing dontrunfile to prevent automatic restart")
            run = 0
            dontrunfile = open(dontRunFilePath, "w")
            dontrunfile.write("1")
            dontrunfile.close()
            continue
        elif messageType == "quit":  # quit instruction received. Probably sent by another brewpi script instance
            logMessage("quit message received on socket. Stopping script.")
            run = 0
            # Leave dontrunfile alone.
            # This instruction is meant to restart the script or replace it with another instance.
            continue
        elif messageType == "eraseLogs":
            # TODO - Update the logfile code to support multiple installs
            # erase the log files for stderr and stdout
            open(util.scriptPath() + '/logs/stderr.txt', 'wb').close()
            open(util.scriptPath() + '/logs/stdout.txt', 'wb').close()
            logMessage("Fresh start! Log files erased.")
            continue
        elif messageType == "interval":  # new interval received
            newInterval = int(value)
            if 5 < newInterval < 5000:
                try:
                    config = util.configSet(configFile, dbConfig, 'interval', float(newInterval))
                except ValueError:
                    logMessage("Cannot convert interval '" + value + "' to float")
                    continue
                logMessage("Notification: Interval changed to " + str(newInterval) + " seconds")
        elif messageType == "startNewBrew":  # new beer name
            newName = value
            result = startNewBrew(newName)
            conn.send(json.dumps(result))
        elif messageType == "pauseLogging":
            result = pauseLogging()
            conn.send(json.dumps(result))
        elif messageType == "stopLogging":
            result = stopLogging()
            conn.send(json.dumps(result))
        elif messageType == "resumeLogging":
            result = resumeLogging()
            conn.send(json.dumps(result))
        elif messageType == "dateTimeFormatDisplay":
            # TODO - Check if this is really necessary on a non-brewpi-www install
            config = util.configSet(configFile, dbConfig, 'dateTimeFormatDisplay', value)
            changeWwwSetting('dateTimeFormatDisplay', value)
            logMessage("Changing date format config setting: " + value)
        elif messageType == "setActiveProfile":
            # TODO - Rewrite beer profile code to use database
            # copy the profile CSV file to the working directory
            logMessage("Setting profile '%s' as active profile" % value)
            config = util.configSet(configFile, dbConfig, 'profileName', value)
            changeWwwSetting('profileName', value)
            profileSrcFile = util.addSlash(config['wwwPath']) + "data/profiles/" + value + ".csv"
            profileDestFile = util.addSlash(util.scriptPath()) + 'settings/tempProfile.csv'
            profileDestFileOld = profileDestFile + '.old'
            try:
                if os.path.isfile(profileDestFile):
                    if os.path.isfile(profileDestFileOld):
                        os.remove(profileDestFileOld)
                    os.rename(profileDestFile, profileDestFileOld)
                shutil.copy(profileSrcFile, profileDestFile)
                # for now, store profile name in header row (in an additional column)
                with file(profileDestFile, 'r') as original:
                    line1 = original.readline().rstrip("\n")
                    rest = original.read()
                with file(profileDestFile, 'w') as modified:
                    modified.write(line1 + "," + value + "\n" + rest)
            except IOError as e:  # catch all exceptions and report back an error
                error = "I/O Error(%d) updating profile: %s " % (e.errno, e.strerror)
                conn.send(error)
                printStdErr(error)
            else:
                conn.send("Profile successfully updated")
                if cs['mode'] is not 'p':
                    cs['mode'] = 'p'
                    bg_ser.writeln("j{mode:p}")
                    logMessage("Notification: Profile mode enabled")
                    raise socket.timeout  # go to serial communication to update controller
        elif messageType == "programController" or messageType == "programArduino":
            if bg_ser is not None:
                bg_ser.stop()
            if ser is not None:
                if ser.isOpen():
                    ser.close()  # close serial port before programming
                ser = None
            try:
                programParameters = json.loads(value)
                hexFile = programParameters['fileName']
                boardType = programParameters['boardType']
                restoreSettings = programParameters['restoreSettings']
                restoreDevices = programParameters['restoreDevices']
                programmer.programController(config, boardType, hexFile, None, None, False,
                                          {'settings': restoreSettings, 'devices': restoreDevices})
                logMessage("New program uploaded to controller, script will restart")
            except json.JSONDecodeError:
                logMessage("Error: cannot decode programming parameters: " + value)
                logMessage("Restarting script without programming.")

            # restart the script when done. This replaces this process with the new one
            time.sleep(5)  # give the controller time to reboot
            python = sys.executable
            os.execl(python, python, *sys.argv)
        elif messageType == "refreshDeviceList":
            deviceList['listState'] = ""  # invalidate local copy
            if value.find("readValues") != -1:
                bg_ser.writeln("d{r:1}")  # request installed devices
                bg_ser.writeln("h{u:-1,v:1}")  # request available, but not installed devices
            else:
                bg_ser.writeln("d{}")  # request installed devices
                bg_ser.writeln("h{u:-1}")  # request available, but not installed devices
        elif messageType == "getDeviceList":
            if deviceList['listState'] in ["dh", "hd"]:
                response = dict(board=hwVersion.board,
                                shield=hwVersion.shield,
                                deviceList=deviceList,
                                pinList=pinList.getPinList(hwVersion.board, hwVersion.shield))
                conn.send(json.dumps(response))
            else:
                conn.send("device-list-not-up-to-date")
        elif messageType == "applyDevice":
            try:
                configStringJson = json.loads(value)  # load as JSON to check syntax
            except json.JSONDecodeError:
                logMessage("Error: invalid JSON parameter string received: " + value)
                continue
            bg_ser.writeln("U" + json.dumps(configStringJson))
            deviceList['listState'] = ""  # invalidate local copy
        elif messageType == "writeDevice":
            try:
                configStringJson = json.loads(value)  # load as JSON to check syntax
            except json.JSONDecodeError:
                logMessage("Error: invalid JSON parameter string received: " + value)
                continue
            bg_ser.writeln("d" + json.dumps(configStringJson))
        elif messageType == "getVersion":
            if hwVersion:
                response = hwVersion.__dict__
                # replace LooseVersion with string, because it is not JSON serializable
                response['version'] = hwVersion.toString()
            else:
                response = {}
            response_str = json.dumps(response)
            conn.send(response_str)
        elif messageType == "resetController":
            logMessage("Resetting controller to factory defaults")
            bg_ser.writeln("E")
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
            bg_ser.writeln('l')

        if(time.time() - prevSettingsUpdate) > 60:
            # Request Settings from controller to stay up to date
            # Controller should send updates on changes, this is a periodical update to ensure it is up to date
            prevSettingsUpdate += 5 # give the controller some time to respond
            bg_ser.writeln('s')

        # if no new data has been received for serialRequestInteval seconds
        if (time.time() - prevDataTime) >= float(config['interval']):
            bg_ser.writeln("t")  # request new from controller
            prevDataTime += 5 # give the controller some time to respond to prevent requesting twice

        elif (time.time() - prevDataTime) > float(config['interval']) + 2 * float(config['interval']):
            #something is wrong: controller is not responding to data requests
            logMessage("Error: controller is not responding to new data requests")


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

                        # If we're saving to the flat files (json/csv), then do so
                        if tempLogType == "flatfile" or tempLogType == "both":
                            # add to JSON file
                            brewpiJson.addRow(localJsonFileName, newRow)
                            #write csv file too
                            csvFile = open(localCsvFileName, "a")
                            try:
                                lineToWrite = (time.strftime("%b %d %Y %H:%M:%S;") +
                                               json.dumps(newRow['BeerTemp']) + ';' +
                                               json.dumps(newRow['BeerSet']) + ';' +
                                               json.dumps(newRow['BeerAnn']) + ';' +
                                               json.dumps(newRow['FridgeTemp']) + ';' +
                                               json.dumps(newRow['FridgeSet']) + ';' +
                                               json.dumps(newRow['FridgeAnn']) + ';' +
                                               json.dumps(newRow['State']) + ';' +
                                               json.dumps(newRow['RoomTemp']) + '\n')
                                csvFile.write(lineToWrite)
                            except KeyError, e:
                                logMessage("KeyError in line from controller: %s" % str(e))

                            csvFile.close()
                            if config.get('use_brewpi_www', True):  # If we don't have a PHP-based brewpi-www installed, we don't use this code
                                # copy to www dir.
                                # Do not write directly to www dir to prevent blocking www file.
                                shutil.copyfile(localJsonFileName, wwwJsonFileName)
                                shutil.copyfile(localCsvFileName, wwwCsvFileName)

                        # If we're saving to the database, do that as well. Breaking out the code to simplify.
                        if tempLogType == "db" or tempLogType == "both":
                            util.save_beer_log_point(dbConfig, newRow)

                    elif line[0] == 'D':
                        # debug message received, should already been filtered out, but print anyway here.
                        logMessage("Finding a log message here should not be possible, report to the devs!")
                        logMessage("Line received was: {0}".format(line))
                    elif line[0] == 'L':
                        # lcd content received
                        prevLcdUpdate = time.time()
                        lcdText = json.loads(line[2:])
                    elif line[0] == 'C':
                        # Control constants received
                        cc = json.loads(line[2:])
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
                        logMessage("Installed devices received: " + json.dumps(deviceList['installed']).encode('utf-8'))
                    elif line[0] == 'U':
                        logMessage("Device updated to: " + line[2:])
                    else:
                        logMessage("Cannot process line from controller: " + line)
                    # end or processing a line
                except json.decoder.JSONDecodeError, e:
                    logMessage("JSON decode error: %s" % str(e))
                    logMessage("Line received was: " + line)
                bg_ser.line_was_processed()  # Clean out the queue
            if message is not None:
                try:
                    expandedMessage = expandLogMessage.expandLogMessage(message)
                    logMessage("Controller debug message: " + expandedMessage)
                except Exception, e:  # catch all exceptions, because out of date file could cause errors
                    logMessage("Error while expanding log message '" + message + "'" + str(e))
                bg_ser.message_was_processed()  # Clean out the queue

        # Check for update from temperature profile
        if cs['mode'] == 'p':  # TODO - Update beer profile mode to work
            newTemp = temperatureProfile.getNewTemp(util.scriptPath())
            if newTemp != cs['beerSet']:
                cs['beerSet'] = newTemp
                # if temperature has to be updated send settings to controller
                bg_ser.writeln("j{beerSet:" + json.dumps(cs['beerSet']) + "}")

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

