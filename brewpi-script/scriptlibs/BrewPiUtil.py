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
from .brewpiScriptConfig import BrewPiScriptConfig


def addSlash(path):
    """
    Adds a slash to the path, but only when it does not already have a slash at the end
    Params: a string
    Returns: a string
    """
    if not path.endswith('/'):
        path += '/'
    return path


def printStdErr(*objs):
    print("", *objs, file=sys.stderr, flush=True)


def logMessage(message):
    """
    Prints a timestamped message to stderr
    """
    if message is None:
        message = "<None>"
    printStdErr(time.strftime("%b %d %Y %H:%M:%S   ") + message)


def scriptPath():  # TODO - Get rid of this! (need to pass in paths to the brewpi-script instance)
    """
    Return the path of BrewPiUtil.py. __file__ only works in modules, not in the main script.
    That is why this function is needed.
    """
    return os.path.dirname(__file__)


def findSerialPort(bootLoader):
    (port, name) = autoSerial.detect_port(bootLoader)
    return port


def setupSerial(dbConfig: BrewPiScriptConfig, baud_rate: int = 57600, time_out: float = 0.1):
    ser = None
    # dumpSerial = config.get('dumpSerial', False)
    dumpSerial = False

    error = None

    # open serial port
    tries = 0
    connection_type = dbConfig.connection_type
    if connection_type == BrewPiScriptConfig.CONNECTION_TYPE_SERIAL or connection_type == BrewPiScriptConfig.CONNECTION_TYPE_AUTO:
        if connection_type == BrewPiScriptConfig.CONNECTION_TYPE_AUTO:
            logMessage("Connection type set to 'auto' - Attempting serial first")
        else:
            logMessage("Connection type Serial selected. Opening serial port.")
        while tries < 10:
            error = ""
            ports_to_try = []

            # If we have a udevPort (from a dbconfig object, found via the udev serial number) use that as the first
            # option - replacing config['port'].
            udev_port = dbConfig.get_port_from_udev()
            if udev_port is not None:
                ports_to_try.append(udev_port)
            else:
                ports_to_try.append(dbConfig.serial_port)

            # Regardless of if we have 'udevPort', add altport as well
            if dbConfig.serial_alt_port:
                ports_to_try.append(dbConfig.serial_alt_port)

            for portSetting in ports_to_try:
                if portSetting == None or portSetting == 'None' or portSetting == "none" or portSetting == "":
                    continue  # skip None setting
                if portSetting == "auto":
                    port = findSerialPort(bootLoader=False)
                    if not port:
                        error = "Could not find compatible serial devices \n"
                        continue  # continue with altport
                else:
                    port = portSetting
                try:
                    ser = serial.Serial(port, baudrate=baud_rate, timeout=time_out, write_timeout=0)
                    if ser:
                        logMessage(f"Connected via serial to port {port}")
                        break
                except (IOError, OSError, serial.SerialException) as e:
                    # error += '0}.\n({1})'.format(portSetting, str(e))
                    error += str(e) + '\n'
            if ser:
                break
            tries += 1
            time.sleep(1)  # TODO - Make sure this is OK

    if connection_type == BrewPiScriptConfig.CONNECTION_TYPE_WIFI or connection_type == BrewPiScriptConfig.CONNECTION_TYPE_AUTO:
        if not ser:
            tries = 0
            if connection_type == BrewPiScriptConfig.CONNECTION_TYPE_AUTO:
                logMessage("No serial attached BrewPi found.  Trying TCP serial (WiFi)")
            else:
                logMessage("Connection type WiFi selected.  Trying TCP serial (WiFi)")
            while tries < 10:
                error = ""

                if dbConfig.wifi_port is None:
                    logMessage(f"Invalid WiFi configuration - Port '{dbConfig.wifi_port}' cannot be converted to integer")
                    logMessage("Exiting.")
                    exit(1)
                port = dbConfig.wifi_port

                ip_address = dbConfig.get_cached_ip()  # Resolve wifi_host to an IP address or get the cached IP

                if ip_address is None:
                    logMessage(f"Invalid WiFi configuration - Cannot resolve wifi_host '{dbConfig.wifi_host}' and no wifi_host_ip set")
                    logMessage("Exiting.")
                    exit(1)

                if not dbConfig.wifi_host:
                    # If we don't have a hostname at all, set it to None
                    hostname = None
                else:
                    hostname = dbConfig.wifi_host

                # The way TCPSerial is implemented, hostname is just a memo field. We always connect to the host (which
                # in this case is a resolved IP address)
                ser = tcpSerial.TCPSerial(host=ip_address, port=port, hostname=hostname)

                if ser:
                    break
                tries += 1
                time.sleep(1)  # TODO - Make sure this is OK

    if not ser:  # At this point, we've tried both serial & WiFi. Need to die.
        logMessage("Unable to connect via Serial or WiFi. Exiting.")
        exit(1)  # TODO - Change this to raise

    if ser:
        # discard everything in serial buffers
        ser.flushInput()
        ser.flushOutput()
    else:
        logMessage("Errors while opening serial port: \n" + error)
        sys.exit(0)  # Die if we weren't able to connect
        # TODO - Change the above to raise

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
