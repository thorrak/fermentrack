#!/usr/bin/python
# Copyright 2015 BrewPi, Elco Jacobs
# This file is part of BrewPi.

# BrewPi is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# BrewPi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with BrewPi. If not, see <http://www.gnu.org/licenses/>.


from __future__ import print_function
import sys
import os
import subprocess

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..") # append parent directory to be able to import files
import autoSerial

# print everything in this file to stderr so it ends up in the correct log file for the web UI
def printStdErr(*objs):
    print("", *objs, file=sys.stderr)

# Quits all running instances of BrewPi
def quitBrewPi(webPath):
    # TODO - Update this to work with pidFiles
    import BrewPiProcess
    allProcesses = BrewPiProcess.BrewPiProcesses()
    allProcesses.stopAll(webPath + "/do_not_run_brewpi")


def updateFromGitHub(userInput, beta, useDfu, restoreSettings = True, restoreDevices = True):
    import BrewPiUtil as util
    from gitHubReleases import gitHubReleases
    import brewpiVersion
    import programController as programmer

    configFile = util.scriptPath() + '/settings/config.cfg'
    # TODO - Update this to work with the database
    config = util.readCfgWithDefaults(configFile)

    printStdErr("Stopping any running instances of BrewPi to check/update controller...")
    quitBrewPi(config['wwwPath'])  # TODO - Fix this, as wwwPath is not set for dbConfig-configured controllers

    hwVersion = None
    shield = None
    board = None
    family = None
    ser = None

    ### Get version number
    printStdErr("\nChecking current firmware version...")
    try:
        ser = util.setupSerial(config)
        hwVersion = brewpiVersion.getVersionFromSerial(ser)
        family = hwVersion.family
        shield = hwVersion.shield
        board = hwVersion.board

        printStdErr("Found " + hwVersion.toExtendedString() + \
               " on port " + ser.name + "\n")
    except:
        if hwVersion is None:
            printStdErr("Unable to receive version from controller.\n"
                        "Is your controller unresponsive and do you wish to try restoring your firmware? [y/N]: ")
            choice = raw_input()
            if not any(choice == x for x in ["yes", "Yes", "YES", "yes", "y", "Y"]):
                printStdErr("Please make sure your controller is connected properly and try again.")
                return 0
            port, name = autoSerial.detect_port()
            if not port:
                printStdErr("Could not find compatible device in available serial ports.")
                return 0
            if "Particle" in name:
                family = "Particle"
                if "Photon" in name:
                    board = 'photon'
                elif "Core" in name:
                    board = 'core'
            elif "Arduino" in name:
                family = "Arduino"
                if "Leonardo" in name:
                    board = 'leonardo'
                elif "Uno" in name:
                    board = 'uno'

            if board is None:
                printStdErr("Unable to connect to controller, perhaps it is disconnected or otherwise unavailable.")
                return -1
            else:
                printStdErr("Will try to restore the firmware on your %s" % name)
                if family == "Arduino":
                    printStdErr("Assuming a Rev C shield. If this is not the case, please program your Arduino manually")
                    shield = 'RevC'
                else:
                    printStdErr("Please put your controller in DFU mode now by holding the setup button during reset, until the LED blinks yellow.")
                    printStdErr("Press Enter when ready.")
                    choice = raw_input()
                    useDfu = True # use dfu mode when board is not responding to serial

    if ser:
        ser.close()  # close serial port
        ser = None

    if hwVersion:
        printStdErr("Current firmware version on controller: " + hwVersion.toString())
    else:
        restoreDevices = False
        restoreSettings = False

    printStdErr("\nChecking GitHub for available release...")
    releases = gitHubReleases("https://api.github.com/repos/BrewPi/firmware")

    availableTags = releases.getTags(beta)
    stableTags = releases.getTags(False)
    compatibleTags = []
    for tag in availableTags:
        url = None
        if family == "Arduino":
            url = releases.getBinUrl(tag, [board, shield, ".hex"])
        elif family == "Spark" or family == "Particle":
            url = releases.getBinUrl(tag, [board, 'brewpi', '.bin'])
        if url is not None:
            compatibleTags.append(tag)

    if len(compatibleTags) == 0:
        printStdErr("No compatible releases found for %s %s" % (family, board))
        return -1

    # default tag is latest stable tag, or latest unstable tag if no stable tag is found
    default_choice = next((i for i, t in enumerate(compatibleTags) if t in stableTags), compatibleTags[0])
    tag = compatibleTags[default_choice]

    if userInput:
        print("\nAvailable releases:\n")
        for i, menu_tag in enumerate(compatibleTags):
            print("[%d] %s" % (i, menu_tag))
        print ("[" + str(len(compatibleTags)) + "] Cancel firmware update")
        num_choices = len(compatibleTags)
        while 1:
            try:
                choice = raw_input("Enter the number [0-%d] of the version you want to program [default = %d (%s)]: " %
                                   (num_choices, default_choice, tag))
                if choice == "":
                    break
                else:
                    selection = int(choice)
            except ValueError:
                print("Use the number! [0-%d]" % num_choices)
                continue
            if selection == num_choices:
                return False # choice = skip updating
            try:
                tag = compatibleTags[selection]
            except IndexError:
                print("Not a valid choice. Try again")
                continue
            break
    else:
        printStdErr("Latest version on GitHub: " + tag)

    if hwVersion is not None and not hwVersion.isNewer(tag):
        if hwVersion.isEqual(tag):
            printStdErr("You are already running version %s." % tag)
        else:
            printStdErr("Your current version is newer than %s." % tag)

        if userInput:
            printStdErr("If you are encountering problems, you can reprogram anyway."
                        " Would you like to do this?"
                        "\nType yes to reprogram or just press enter to keep your current firmware: ")
            choice = raw_input()
            if not any(choice == x for x in ["yes", "Yes", "YES", "yes", "y", "Y"]):
                return 0
        else:
            printStdErr("No update needed. Exiting.")
            exit(0)


    if hwVersion is not None and userInput:
        printStdErr("Would you like me to try to restore you settings after programming? [Y/n]: ")
        choice = raw_input()
        if not any(choice == x for x in ["", "yes", "Yes", "YES", "yes", "y", "Y"]):
            restoreSettings = False
        printStdErr("Would you like me to try to restore your configured devices after programming? [Y/n]: ")
        choice = raw_input()
        if not any(choice == x for x in ["", "yes", "Yes", "YES", "yes", "y", "Y"]):
            restoreDevices = False

    printStdErr("Downloading firmware...")
    localFileName = None
    system1 = None
    system2 = None

    if family == "Arduino":
        localFileName = releases.getBin(tag, [board, shield, ".hex"])
    elif family == "Spark" or family == "Particle":
        localFileName = releases.getBin(tag, [board, 'brewpi', '.bin'])
    else:
        printStdErr("Error: Device family {0} not recognized".format(family))
        return -1

    if board == "photon":
        if hwVersion:
            oldVersion = hwVersion.version.vstring
        else:
            oldVersion = "0.0.0"
        latestSystemTag = releases.getLatestTagForSystem(prerelease=beta, since=oldVersion)
        if latestSystemTag is not None:
            printStdErr("Updated system firmware for the photon found in release {0}".format(latestSystemTag))
            system1 = releases.getBin(latestSystemTag, ['photon', 'system-part1', '.bin'])
            system2 = releases.getBin(latestSystemTag, ['photon', 'system-part2', '.bin'])
            if system1:
                printStdErr("Downloaded new system firmware to:\n")
                printStdErr("{0}\nand\n".format(system1))
                if system2:
                    printStdErr("{0}\n".format(system2))
                else:
                    printStdErr("Error: system firmware part2 not found in release")
                    return -1
        else:
            printStdErr("Photon system firmware is up to date.\n")

    if localFileName:
        printStdErr("Latest firmware downloaded to:\n" + localFileName)
    else:
        printStdErr("Downloading firmware failed")
        return -1

    printStdErr("\nUpdating firmware...\n")
    result = programmer.programController(config, board, localFileName, system1, system2, useDfu,
                                          {'settings': restoreSettings, 'devices': restoreDevices})
    util.removeDontRunFile(config['wwwPath'] + "/do_not_run_brewpi")
    return result

if __name__ == '__main__':
    print("updateFirmware.py is disabled in this version of brewpi-script. Please update your firmware manually, or using Fermentrack")
    sys.exit()

    import getopt
    # Read in command line arguments
    try:
        opts, args = getopt.getopt(sys.argv[1:], "asd", ['beta', 'silent', 'dfu'])
    except getopt.GetoptError:
        print ("Unknown parameter, available options: \n" +
              "--silent\t use default options, do not ask for user input \n" +
              "--beta\t\t include unstable (prerelease) releases \n")
        sys.exit()

    userInput = True
    beta = False
    useDfu = False

    for o, a in opts:
        # print help message for command line options
        if o in ('-s', '--silent'):
            userInput = False
        if o in ('-b', '--beta'):
            beta = True
        if o in ('-d', '--dfu'):
            useDfu = True


    result = updateFromGitHub(userInput=userInput, beta=beta, useDfu=useDfu)
    exit(result)