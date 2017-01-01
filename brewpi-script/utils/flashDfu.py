# Copyright 2015 BrewPi
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

import sys
# Check needed software dependencies to nudge users to fix their setup
if sys.version_info < (2, 7):
    print "Sorry, requires Python 2.7."
    sys.exit(1)

import distutils.spawn
import time
import os
import platform
import getopt
import subprocess
import re
from distutils.version import LooseVersion
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..") # append parent directory to be able to import files
from gitHubReleases import gitHubReleases
import BrewPiUtil as util
import autoSerial
import serial
from programController import SerialProgrammer

releases = gitHubReleases("https://api.github.com/repos/brewpi/firmware")

serialPorts = []

def printHelp():
        print "\n Available command line options: "
        print "--help\t\t print this help message"
        print "--tag=\t\t specify which tag to download from github"
        print "--file=\t\t path to .bin file to flash instead of the latest release on GitHub.\n" \
              "\t\t If this is a directory, search for binary and system update files."
        print "--system=\t path to directory containing system binaries to update the system firmware on the photon."
        print "--system1=\t path to binary for system part 1."
        print "--system2=\t path to binary for system part 2."
        print "--multi\t\t keep the script alive to flash multiple devices"
        print "--autodfu\t automatically reboot photon in DFU mode by opening serial port at 14400 baud"
        print "--testmode\t set controller to test mode after flashing"
        print "--noreset\t do not reset EEPROM after flashing"



# Read in command line arguments
try:
    opts, args = getopt.getopt(sys.argv[1:], "hf:t:ma",
                               ['help', 'file=', 'system=', 'system1=', 'system2=',
                                'multi', 'tag=', 'testmode', 'autodfu', 'testmode', 'noreset'])
except getopt.GetoptError:
    print("Unknown parameter")
    printHelp()
    sys.exit()

multi = False
testMode = False
autoDfu = False
noReset = False
tag = None
# binaries for system update
system1 = None
system2 = None
# binary to flash
binFile = None




for o, a in opts:
    # print help message for command line options
    if o in ('-h', '--help'):
        printHelp()

        exit()
    # supply a binary file
    if o in ('-f', '--file'):
        print("Using local files instead of downloading a release. \n")
        if not os.path.isfile(a) and os.path.isdir(a):
            for file in os.listdir(a):
                if all(x in file for x in ['brewpi', '.bin']):
                    binFile = os.path.join(os.path.abspath(a), file)
        else:
            binFile = os.path.abspath(a)
        if not os.path.exists(binFile):
            print('ERROR: Binary file "%s" was not found!' % binFile)
            exit(1)
    # supply a system update directory
    if o in ('-s', '--system'):
        print("Using local files for system update instead of downloading from GitHub.\n")
        if os.path.isdir(a):
            for file in os.listdir(a):
                if all(x in file for x in ['system', 'part1', '.bin']):
                    system1 = os.path.join(os.path.abspath(a), file)
                if all(x in file for x in ['system', 'part2', '.bin']):
                    system2 = os.path.join(os.path.abspath(a), file)
        else:
            print('ERROR: System binaries location {0} is not a directory!' % a)
        if not os.path.exists(system1):
            print('ERROR: System binary 1 "%s" was not found!' % system1)
            exit(1)
        if not os.path.exists(system2):
            print('ERROR: System binary 2 "%s" was not found!' % system2)
            exit(1)
    if o in ('--system1'):
        system1 = a
        if not os.path.exists(system1):
            print('ERROR: System binary 1 "%s" was not found!' % a)
            exit(1)
    if o in ('--system2'):
        system2 = a
        if not os.path.exists(system2):
            print('ERROR: System binary 2 "%s" was not found!' % a)
            exit(1)
    if o in ('-m', '--multi'):
        multi = True
        print "Started in multi flash mode"
    if o in ('-t', '--tag'):
        tag = a
        print "Will try to download release '{0}'".format(tag)
    if o in ('--testmode'):
        testMode = True
        print "Will set device to test mode after flashing"
    if o in ('-a', '--autodfu'):
        autoDfu = True
        print "Will automatically reboot newly detected photons into DFU mode"
    if o in ('--noreset'):
        noReset = True

dfuPath = "dfu-util"
# check whether dfu-util can be found
if distutils.spawn.find_executable('dfu-util') is None:
    if platform.system() == "Windows":
        p = subprocess.Popen("where dfu-util", stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        p.wait()
        output, errors = p.communicate()
        if not output:
            print "dfu-util cannot be found, please add its location to your PATH variable"
            exit(1)
    elif platform.system() == "Linux":
        # TODO: change this block to be platform / architecture agnositc
        # as it currently expects you to be running from a Pi
        downloadDir = os.path.join(os.path.dirname(__file__), "downloads/")
        dfuPath = os.path.join(downloadDir, "dfu-util")
        if not os.path.exists(dfuPath):
            print "dfu-util not found, downloading dfu-util..."
            dfuUrl = "http://dfu-util.sourceforge.net/releases/dfu-util-0.7-binaries/linux-armel/dfu-util"
            if not os.path.exists(downloadDir):
                os.makedirs(downloadDir, 0777)
            releases.download(dfuUrl, downloadDir)
            os.chmod(dfuPath, 0777) # make executable
        else:
            print "Using dfu-util binary at " + dfuPath
    else:
        print "This script is written for Linux or Windows only. We'll gladly take pull requests for other platforms."
        exit(1)
else:
    p = subprocess.Popen("dfu-util -V", stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    p.wait()
    output, errors = p.communicate()
    dfuUtilVersion =  re.search('(?<=dfu-util\\s)\\S*', output).group()
    if not dfuUtilVersion:
        print "Cannot determine installed version of dfu-util. Exiting"
        exit(1)
    else:
        print "dfu-util version {0} found installed on system.".format(dfuUtilVersion)

    if LooseVersion(dfuUtilVersion) < LooseVersion('0.7'):
        print "Your installed version of dfu-util ({0}) is too old.\n".format(dfuUtilVersion)
        print "A minimum of version 0.7 is required. If you are on a Raspberry Pi, we can download the correct version automatically.\n"
        print "Just uninstall your system version with: sudo apt-get remove dfu-util\n"
        print "Then try again."
        exit(1)

firstLoop = True
print "Detecting DFU devices"
while(True):
    # list DFU devices to see whether a device is connected
    p = subprocess.Popen(dfuPath + " -l", stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    p.wait()
    output, errors = p.communicate()
    if errors:
        print errors

    DFUs = re.findall(r'\[([0-9a-f]{4}:[0-9a-f]{4})\].*alt=0', output) # find hex format [0123:abcd]
    if len(DFUs) > 0:
        print "Found {0} devices: ".format(len(DFUs)), DFUs

    if len(DFUs) > 1:
        print "Please only connect one device at a time and try again."
        exit(1)
    elif len(DFUs) == 1:

        if DFUs[0] == '1d50:607f':
            type = 'core'
            print "Device identified as Spark Core"
        elif DFUs[0] == '2b04:d006':
            type = 'photon'
            print "Device identified as Particle Photon"
        else:
            print "Could not identify device as Photon or Spark Core. Exiting"
            exit(1)

        # download latest binary from GitHub if file not specified
        if not binFile:
            if tag is None:
                print "Downloading latest firmware..."
                tag = releases.getLatestTag(type, False)
                print "Latest stable version on GitHub: " + tag
            else:
                print "Downloading release " + tag

            binFile = releases.getBin(tag, [type, 'brewpi', '.bin'])
            if binFile:
                print "Firmware downloaded to " + binFile
            else:
                print "Could not find download in release {0} with these words in the file name: {1}".format(tag, type)
                exit(1)

            if type == 'photon':
                if not releases.containsSystemImage(tag):
                    # if the release is a pre-release, also include pre-releases when searching for latest system image
                    prerelease = releases.findByTag(tag)['prerelease']
                    latestSystemTag = releases.getLatestTagForSystem(prerelease)
                else:

                    latestSystemTag = tag
                print ("Updated system firmware for the photon found in release {0}".format(latestSystemTag))
                system1 = releases.getBin(latestSystemTag, ['photon', 'system-part1', '.bin'])
                system2 = releases.getBin(latestSystemTag, ['photon', 'system-part2', '.bin'])
                if system1:
                    print "Downloaded new system firmware to:\n"
                    print "{0} and\n".format(system1)
                    if not system2:
                        print "Error: system firmware part2 not found in release"
                        exit(1)
                    else:
                        print "{0}\n".format(system2)


        if binFile:
            if type == 'core':
                print "Now writing BrewPi firmware {0}".format(binFile)
                p = subprocess.Popen(dfuPath + " -d 1d50:607f -a 0 -s 0x08005000:leave -D {0}".format(binFile), shell=True)
                p.wait()
            elif type == 'photon':
                if system1 and system2:
                    print "First updating system firmware for the Photon, part 1: {0}".format(system1)
                    p = subprocess.Popen(dfuPath + " -d 2b04:d006 -a 0 -s 0x8020000 -D {0}".format(system1), shell=True)
                    p.wait()
                    print "Continuing updating system firmware for the Photon, part 2: {0}".format(system2)
                    p = subprocess.Popen(dfuPath + " -d 2b04:d006 -a 0 -s 0x8060000 -D {0}".format(system2), shell=True)
                    p.wait()

                print "Now writing BrewPi firmware {0}".format(binFile)
                p = subprocess.Popen(dfuPath + " -d 0x2B04:0xD006 -a 0 -s 0x80A0000:leave -D {0}".format(binFile), shell=True)
                p.wait()

            print "Programming done"

            if not noReset:
                print "Now resetting EEPROM to defaults"
                # reset EEPROM to defaults
                configFile = util.scriptPath() + '/settings/config.cfg'
                config = util.readCfgWithDefaults(configFile)
                programmer = SerialProgrammer.create(config, type)

                # open serial port
                print "Opening serial port"
                if not programmer.open_serial_with_retry(config, 57600, 1):
                    print "Could not open serial port after programming"
                else:
                    programmer.fetch_version("Success! ")
                    time.sleep(5)
                    programmer.reset_settings(testMode)
                    serialPorts = list(autoSerial.find_compatible_serial_ports()) # update serial ports here so device will not be seen as new

        else:
            print "found DFU device, but no binary specified for flashing"
        if not multi:
            break
    else:
        if firstLoop:
            print "Did not find any DFU devices."
            print "Is your Photon or Spark Core running in DFU mode (blinking yellow)?"
            print "Waiting until a DFU device is connected..."
        firstLoop = False
        if autoDfu:
            previousSerialPorts = serialPorts
            serialPorts = list(autoSerial.find_compatible_serial_ports())
            newPorts = list(set(serialPorts) - set(previousSerialPorts))
            if len(newPorts):
                print "Found new serial port connected: {0}".format(newPorts[0])
                port = newPorts[0][0]
                name = newPorts[0][1]
                if name == "Particle Photon":
                    print "Putting Photon in DFU mode"
                    ser = serial.Serial(port)
                    try:
                        ser.baudrate = 14400 # this triggers a reboot in DFU mode
                        ser.baudrate = 57600 # don't leave serial port at 14400, or a second reboot into DFU will be triggered later
                        ser.close()
                    except serial.serialutil.SerialException, ValueError:
                        pass # because device reboots while reconfiguring an exception is thrown, ignore
                    if ser.isOpen():
                        ser.close()
                    ser.baudrate = 57600 # don't leave serial port at 14400, or a reboot will be triggered later
                else:
                    print "Automatically rebooting in DFU mode is not supported for {0}".format(name)



    time.sleep(1)
