# Copyright 2013 BrewPi
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
import time
import sys
import os
import serial
from . import autoSerial
from . import tcpSerial


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# This is so Django knows where to find stuff.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fermentrack_django.settings")
sys.path.append(BASE_DIR)

# This is so my local_settings.py gets loaded.
os.chdir(BASE_DIR)

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
import app.models as models  # This is only applicable if we're working with Django-based models


# try:
#     import configobj
# except ImportError:
#     print("BrewPi requires ConfigObj to run, please install it with 'sudo apt-get install python-configobj")
#     sys.exit(0)


def addSlash(path):
    """
    Adds a slash to the path, but only when it does not already have a slash at the end
    Params: a string
    Returns: a string
    """
    if not path.endswith('/'):
        path += '/'
    return path


def read_config_from_database_without_defaults(db_config_object) -> dict:
    """
    Reads configuration parameters from the database without defaults

    Params:
    db_config_object: models.BrewPiDevice, BrewPiDevice object

    Returns:
    dict of settings
    """

    config = {}

    # Unlike the above, we don't have defaults (because we assume the database enforces defaults). Load everything.
    # config['scriptPath'] = db_config_object.script_path
    config['port'] = db_config_object.serial_port
    # if db_config_object.serial_alt_port != 'None':
    config['altport'] = db_config_object.serial_alt_port
    config['boardType'] = db_config_object.board_type
    config['beerName'] = db_config_object.get_active_beer_name()
    config['interval'] = float(db_config_object.data_point_log_interval)  # Converting to a float to match config file
    config['dataLogging'] = db_config_object.logging_status
    config['socket_name'] = db_config_object.socket_name
    config['connection_type'] = db_config_object.connection_type
    config['wifiHost'] = db_config_object.wifi_host
    config['wifiPort'] = db_config_object.wifi_port
    config['useInetSocket'] = db_config_object.useInetSocket
    config['socketPort'] = db_config_object.socketPort
    config['socketHost'] = db_config_object.socketHost
    config['wifiIPAddress'] = db_config_object.get_cached_ip()  # If we have a cached IP from mDNS, we'll use it

    udevPort = db_config_object.get_port_from_udev()
    if udevPort is None:
        logMessage("Unable to locate device using USB serial number")
    else:
        config['udevPort'] = udevPort  # If we prioritize udev lookup for serial, get the port

    return config


def configSet(db_config_object, settingName, value):
    # Assuming we have a valid db_config_object here
    if settingName == "port":
        db_config_object.serial_port = value
    elif settingName == "altport":
        db_config_object.serial_alt_port = value
    elif settingName == "boardType":
        db_config_object.board_type = value
    elif settingName == "beerName":
        # If we have a blank or NoneType name, we're unsetting the beer.
        if value is None or len(value) < 1:
            db_config_object.active_beer = None
        else:  # Otherwise, we need to (possibly) create the beer and link it to the chamber
            # One thing to note - In traditional brewpi-www the beer is entirely created within/managed by the
            # brewpi-script. For Fermentrack we're
            new_beer, created = models.Beer.objects.get_or_create(name=value, device=db_config_object)
            if created:
                # If we just created the beer, set the temp format (otherwise, defaults to Fahrenheit)
                new_beer.format = db_config_object.temp_format
                new_beer.save()
            if db_config_object.active_beer != new_beer:
                db_config_object.active_beer = new_beer

    elif settingName == "socket_name":
        db_config_object.socket_name = value
    elif settingName == "interval":
        db_config_object.data_point_log_interval = value
    elif settingName == "dataLogging":
        db_config_object.logging_status = value
    else:
        # In all other cases, just try to set the field directly
        setattr(db_config_object, settingName, value)
    db_config_object.save()
    return read_config_from_database_without_defaults(db_config_object)


def save_beer_log_point(db_config_object, beer_row):
    """
    Saves a row of data to the database (mapping the data row we are passed to Django's BeerLogPoint model)
    :param db_config_object:
    :param beer_row:
    :return:
    """
    new_log_point = models.BeerLogPoint()

    new_log_point.beer_temp = beer_row['BeerTemp']
    new_log_point.beer_set = beer_row['BeerSet']
    new_log_point.beer_ann = beer_row['BeerAnn']

    new_log_point.fridge_temp = beer_row['FridgeTemp']
    new_log_point.fridge_set = beer_row['FridgeSet']
    new_log_point.fridge_ann = beer_row['FridgeAnn']

    new_log_point.room_temp = beer_row['RoomTemp']
    new_log_point.state = beer_row['State']

    new_log_point.temp_format = db_config_object.temp_format
    new_log_point.associated_beer = db_config_object.active_beer

    try:
        new_log_point.enrich_gravity_data()  # If gravity sensing is turned on, this will capture & populate everything
    except RuntimeError:
        # This gets tripped when there is an issue with enrich_gravity_data where the associated gravity sensor no longer
        # exists. This shouldn't happen, but can if the user goes poking around. Don't log the point - just return.
        return

    new_log_point.save()


def printStdErr(*objs):
    print("", *objs, file=sys.stderr)

def logMessage(message):
    """
    Prints a timestamped message to stderr
    """
    if message is None:
        message = "<None>"
    printStdErr(time.strftime("%b %d %Y %H:%M:%S   ") + message)


def scriptPath():
    """
    Return the path of BrewPiUtil.py. __file__ only works in modules, not in the main script.
    That is why this function is needed.
    """
    return os.path.dirname(__file__)


def removeDontRunFile(path='/var/www/do_not_run_brewpi'):
    if os.path.isfile(path):
        os.remove(path)
        if not sys.platform.startswith('win'):  # cron not available
            print("BrewPi script will restart automatically.")
    else:
        print("File do_not_run_brewpi does not exist at " + path)

def findSerialPort(bootLoader):
    (port, name) = autoSerial.detect_port(bootLoader)
    return port

def setupSerial(config, baud_rate=57600, time_out=0.1):
    ser = None
    dumpSerial = config.get('dumpSerial', False)

    error = None

    # open serial port
    tries = 0
    connection_type = config.get('connection_type', 'auto')
    if connection_type == "serial" or connection_type == "auto":
        if connection_type == "auto":
            logMessage("Connection type set to 'auto' - Attempting serial first")
        else:
            logMessage("Connection type Serial selected. Opening serial port.")
        while tries < 10:
            error = ""
            ports_to_try = []

            # If we have a udevPort (from a dbconfig object, found via the udev serial number) use that as the first
            # option - replacing config['port'].
            if 'udevPort' in config:
                ports_to_try.append(config['udevPort'])
            else:
                ports_to_try.append(config.get('port', "auto"))

            # Regardless of if we have 'udevPort', add altport as well
            if 'altport' in config:
                ports_to_try.append(config['altport'])

            for portSetting in ports_to_try:
                if portSetting == None or portSetting == 'None' or portSetting == "none":
                    continue  # skip None setting
                if portSetting == "auto":
                    port = findSerialPort(bootLoader=False)
                    if not port:
                        error = "Could not find compatible serial devices \n"
                        continue # continue with altport
                else:
                    port = portSetting
                try:
                    ser = serial.Serial(port, baudrate=baud_rate, timeout=time_out, write_timeout=0)
                    if ser:
                        logMessage("Connected via serial to port {}".format(port))
                        break
                except (IOError, OSError, serial.SerialException) as e:
                    # error += '0}.\n({1})'.format(portSetting, str(e))
                    error += str(e) + '\n'
            if ser:
                break
            tries += 1
            time.sleep(1)

    if connection_type == "wifi" or connection_type == "auto":
        if not(ser):
            tries=0
            if connection_type == "auto":
                logMessage("No serial attached BrewPi found.  Trying TCP serial (WiFi)")
            else:
                logMessage("Connection type WiFi selected.  Trying TCP serial (WiFi)")
            while tries < 10:
                error = ""

                try:
                    port = int(config['wifiPort'])
                except TypeError:
                    logMessage("Invalid WiFi configuration - Port '{}' cannot be converted to integer".format(config['wifiPort']))
                    logMessage("Exiting.")
                    port=0  # to make PyCharm happy
                    exit(1)

                if not(config['wifiHost'] == None or  config['wifiHost'] == 'None' or config['wifiHost'] == 'none'):
                    # We're going to use the wifiIPAddress
                    # TODO - Ensure hostname lookup
                    connect_to = config.get('wifiIPAddress', config['wifiHost'])
                    ser = tcpSerial.TCPSerial(host=connect_to, port=port, hostname=config['wifiHost'])
                else:
                    logMessage("Invalid WiFi configuration:")
                    logMessage("  wifiHost: {}".format(config['wifiHost']))
                    logMessage("  wifiPort: {}".format(config['wifiPort']))
                    logMessage("Exiting.")
                    exit(1)

                if ser:
                    break
                tries += 1
                time.sleep(1)
        if not(ser):  # At this point, we've tried both serial & WiFi. Need to die.
            logMessage("Unable to connect via WiFi. Exiting.")
            exit(1)


    if ser:
        # discard everything in serial buffers
        ser.flushInput()
        ser.flushOutput()
    else:
        logMessage("Errors while opening serial port: \n" + error)
        sys.exit(0)  # Die if we weren't able to connect

    # yes this is monkey patching, but I don't see how to replace the methods on a dynamically instantiated type any other way
    if dumpSerial:
        ser.readOriginal = ser.read
        ser.writeOriginal = ser.write

        def readAndDump(size=1):
            r = ser.readOriginal(size)
            sys.stdout.write(r)
            return r

        def writeAndDump(data):
            ser.writeOriginal(data)
            sys.stderr.write(data)

        ser.read = readAndDump
        ser.write = writeAndDump

    return ser


# remove extended ascii characters from string, because they can raise UnicodeDecodeError later
def asciiToUnicode(s):
    try:
        s_u = unicode(s, 'cp437', 'ignore')
        return s_u.replace(chr(0xB0), '&deg')
    except:
        return s
