# Tilt Hydrometer  Tilt polling library
# Simon Bowler 22/01/2017
# simon@bowler.id.au
#
# Version: 1.5 - Bug fix for debugging log and also adding connection resilliance. Will now reset
#                bluetooth connection if dropped for any reason.
# Version: 1.4 - Added additional resiliance and debugging when parsing configuration files.
#                Also added debug parameter to settings.ini to provide additional logging.
# Version: 1.3 - Upgraded for firmware 0.4.4
# Version: 1.2 - Added ability to get smoothed value, current value (calibrated)
#                and an measure of variance (can indicate vigor of fermentation).
#                Renamed library to reflect new name of product


from __future__ import print_function
import blescan
import sys
import datetime
import time
import os

import bluetooth._bluetooth as bluez
import threading
import thread

import numpy

from scipy.interpolate import interp1d
from scipy import arange, array, exp
import csv
import functools
import ConfigParser

TILTHYDROMETER_COLOURS = ['Red', 'Green', 'Black', 'Purple', 'Orange', 'Blue', 'Yellow', 'Pink']

# Default time in seconds to wait before checking config files to see if calibration data has changed.
DATA_REFRESH_WINDOW = 60


# extrap1d Sourced from sastanin @ StackOverflow:
# http://stackoverflow.com/questions/2745329/how-to-make-scipy-interpolate-give-an-extrapolated-result-beyond-the-input-range
# This function is required as the interp1d function doesn't support extrapolation in the version of scipy that is currently available on the pi.
def extrap1d(interpolator):
    xs = interpolator.x
    ys = interpolator.y

    def pointwise(x):
        if x < xs[0]:
            return ys[0] + (x - xs[0]) * (ys[1] - ys[0]) / (xs[1] - xs[0])
        elif x > xs[-1]:
            return ys[-1] + (x - xs[-1]) * (ys[-1] - ys[-2]) / (xs[-1] - xs[-2])
        else:
            return interpolator(x)

    def ufunclike(xs):
        return array(map(pointwise, array(xs)))

    return ufunclike


# Simple offset calibration if only one point available.
def offsetCalibration(offset, value):
    return value + offset


# More complex interpolation calibration if more than one calibration point available
def extrapolationCalibration(extrapolationFunction, value):
    inputValue = [value]
    returnValue = extrapolationFunction(inputValue)
    return returnValue[0]


def noCalibration(value):
    return value


# Median utility function
def median(values):
    return numpy.median(numpy.array(values))


# Class to hold a TiltHydrometer reading
class TiltHydrometerValue:
    temperature = 0
    gravity = 0
    timestamp = 0

    def __init__(self, temperature, gravity):
        self.temperature = round(temperature, 2)
        self.gravity = round(gravity, 3)
        self.timestamp = datetime.datetime.now()

    def __str__(self):
        return "T: " + str(self.temperature) + " G: " + str(self.gravity)


# TiltHydrometer class, looks after calibration, storing of values and smoothing of read values.
class TiltHydrometer:
    colour = ''
    debug = False
    values = None
    lock = None
    averagingPeriod = 0
    medianWindow = 0
    tempCalibrationFunction = None
    gravityCalibrationFunction = None
    calibrationDataTime = {}

    # Averaging period is number of secs to average across. 0 to disable.
    # Median window is the window to use for applying a median filter accross the values. 0 to disable. Median window should be <= the averaging period.
    # If Median is disabled, the returned value will be the average of all values recorded during the averaging period.
    def __init__(self, colour, averagingPeriod=0, medianWindow=0, debug=False):
        self.colour = colour
        self.lock = threading.Lock()
        self.averagingPeriod = averagingPeriod
        self.medianWindow = medianWindow
        self.debug = debug
        self.values = []
        self.calibrationDataTime = {}
        self.calibrate()

    def calibrate(self):
        """Load/reload calibration functions."""
        # Check for temperature function. If none, then not changed since last load.
        tempFunction = self.tiltHydrometerCalibrationFunction("temperature", self.colour)
        if (tempFunction is not None):
            self.tempCalibrationFunction = tempFunction

        # Check for gravity function. If none, then not changed since last load.
        gravityFunction = self.tiltHydrometerCalibrationFunction("gravity", self.colour)
        if (gravityFunction is not None):
            self.gravityCalibrationFunction = gravityFunction

    def setValues(self, temperature, gravity):
        """Set/add the latest temperature & gravity readings to the store. These values will be calibrated before storing if calibration is enabled"""
        with self.lock:
            self.cleanValues()
            self.calibrate()

            calibratedTemperature = temperature
            calibratedGravity = gravity

            try:
                calibratedTemperature = self.tempCalibrationFunction(temperature)
            except (Exception) as e:
                print("ERROR: TiltHydrometer (" + self.colour + "): Unable to calibrate temperature: " + str(
                    temperature) + " - " + e.message)

            try:
                calibratedGravity = self.gravityCalibrationFunction(gravity)
            except (Exception) as e:
                print("ERROR: TiltHydrometer (" + self.colour + "): Unable to calibrate gravity: " + str(
                    gravity) + " - " + e.message)

            self.values.append(TiltHydrometerValue(calibratedTemperature, calibratedGravity))

    def getValues(self):
        """Returns the temperature & gravity values of the Tilt Hydrometer . This will be the latest read value unless averaging / median has been enabled"""
        with self.lock:
            returnValue = None
            if (len(self.values) > 0):
                if (self.medianWindow == 0):
                    returnValue = self.averageValues()
                else:
                    returnValue = self.medianValues(self.medianWindow)

                self.cleanValues()
        return returnValue

    def averageValues(self):
        """Internal function to average all the stored values"""
        returnValue = None
        if (len(self.values) > 0):
            returnValue = TiltHydrometerValue(0, 0)
            for value in self.values:
                returnValue.temperature += value.temperature
                returnValue.gravity += value.gravity

            # average values
            returnValue.temperature /= len(self.values)
            returnValue.gravity /= len(self.values)

            # round values
            returnValue.temperature = round(returnValue.temperature, 2)
            returnValue.gravity = round(returnValue.gravity, 3)
        return returnValue

    def medianValues(self, window=3):
        """Internal function to use a median method across the stored values to reduce noise.
           window - Smoothing window to apply across the data. If the window is less than the dataset size, the window will be moved across the dataset,
                    taking a median value for each window, with the resultant set averaged"""
        returnValue = None
        # Ensure there are enough values to do a median filter, if not shrink window temporarily
        if (len(self.values) < window):
            window = len(self.values)

        # print("Median filter!")
        returnValue = TiltHydrometerValue(0, 0)

        sidebars = (window - 1) / 2
        medianValueCount = 0

        for i in range(len(self.values) - (window - 1)):
            # Work out range of values to do median. At start and end of assessment, need to pad with start and end values.
            medianValues = self.values[i:i + window]
            medianValuesTemp = []
            medianValuesGravity = []

            # Separate out Temp and Gravity values
            for medianValue in medianValues:
                medianValuesTemp.append(medianValue.temperature)
                medianValuesGravity.append(medianValue.gravity)

            # Add the median value to the running total.
            returnValue.temperature += median(medianValuesTemp)
            returnValue.gravity += median(medianValuesGravity)

            # Increase count
            medianValueCount += 1

        # average values
        returnValue.temperature /= medianValueCount
        returnValue.gravity /= medianValueCount

        # round values
        returnValue.temperature = round(returnValue.temperature, 2)
        returnValue.gravity = round(returnValue.gravity, 3)

        return returnValue

    def cleanValues(self):
        """Function to clean out stale values that are beyond the desired window"""
        nowTime = datetime.datetime.now()

        for value in self.values:
            if ((nowTime - value.timestamp).seconds >= self.averagingPeriod):
                self.values.pop(0)
            else:
                # The list is sorted in chronological order, so once we've hit this condition we can stop searching.
                break

    # Load the calibration settings from file and create the calibration functions
    def tiltHydrometerCalibrationFunction(self, type, colour):
        # This function is replaced under Fermentrack
        returnFunction = noCalibration

        originalValues = []
        actualValues = []
        csvFile = None
        filename = "tiltHydrometer/" + type.upper() + "." + colour.lower()

        # Find out last time we attempted to load.
        lastChecked = self.calibrationDataTime.get(type + "_checked", 0)
        if ((int(time.time()) - lastChecked) < DATA_REFRESH_WINDOW):
            # Only check every x seconds
            return None

        # Retrieve at the last load time.
        lastLoaded = self.calibrationDataTime.get(type, 0)
        self.calibrationDataTime[type + "_checked"] = int(time.time())

        try:
            if (os.path.isfile(filename)):
                fileModificationTime = os.path.getmtime(filename)
                if (lastLoaded >= fileModificationTime):
                    # No need to load, no change
                    return None
                csvFile = open(filename, "rb")
                csvFileReader = csv.reader(csvFile, skipinitialspace=True)
                self.calibrationDataTime[type] = fileModificationTime

                lineNumber = 1
                for row in csvFileReader:
                    if (self.debug):
                        print("TiltHydrometer (" + colour + "): File - " + filename + ", Line " + str(
                            lineNumber) + " processing [" + str(row) + "]")
                    # Skip any comment rows and rows with no configuration data
                    if ((len(row) != 2) or (row[0][:1] == "#")):
                        print("WARNING: TiltHydrometer (" + colour + "): File - " + filename + ", Line " + str(
                            lineNumber) + " was ignored as does not contain valid configuration data [" + str(row) + "]")
                    else:
                        if (self.debug):
                            print("TiltHydrometer (" + colour + "): File - " + filename + ", Line " + str(
                                lineNumber) + " processed successfully")
                        originalValues.append(float(row[0]))
                        actualValues.append(float(row[1]))

                    lineNumber += 1
                # Close file
                csvFile.close()
        except IOError:
            print("TiltHydrometer (" + colour + "):  " + type.capitalize() + ": No calibration data (" + filename + ")")
        except (Exception) as e:
            print("ERROR: TiltHydrometer (" + colour + "): Unable to initialise " + type.capitalize() + " Calibration data (" + filename + ") - " + e.message)
            # Attempt to close the file
            if (csvFile is not None):
                # Close file
                csvFile.close()

        # If more than two values, use interpolation
        if (len(actualValues) >= 2):
            interpolationFunction = interp1d(originalValues, actualValues, bounds_error=False, fill_value=1)
            returnFunction = functools.partial(extrapolationCalibration, extrap1d(interpolationFunction))
            print("TiltHydrometer (" + colour + "): Initialised " + type.capitalize() + " Calibration: Interpolation")
        # Not enough values. Likely just an offset calculation
        elif (len(actualValues) == 1):
            offset = actualValues[0] - originalValues[0]
            returnFunction = functools.partial(offsetCalibration, offset)
            print("TiltHydrometer (" + colour + "): Initialised " + type.capitalize() + " Calibration: Offset (" + str(
                offset) + ")")
        return returnFunction


# Class to manage the monitoring of all TiltHydrometers and storing the read values.
class TiltHydrometerManager:
    inFahrenheit = True
    dev_id = 0
    averagingPeriod = 0
    medianWindow = 0
    debug = False

    scanning = True
    # Dictionary to hold tiltHydrometers - index on colour
    tiltHydrometers = {}

    brewthread = None
    lastLoadTime = 0
    lastCheckedTime = 0

    def __init__(self, inFahrenheit=True, averagingPeriod=0, medianWindow=0, device_id=0):
        self.inFahrenheit = inFahrenheit
        self.dev_id = device_id
        self.averagingPeriod = averagingPeriod
        self.medianWindow = medianWindow

        self.reloadSettings()

    # Convert Tilt UUID back to colour
    def tiltHydrometerName(self, uuid):
        return {
            'a495bb10c5b14b44b5121370f02d74de': 'Red',
            'a495bb20c5b14b44b5121370f02d74de': 'Green',
            'a495bb30c5b14b44b5121370f02d74de': 'Black',
            'a495bb40c5b14b44b5121370f02d74de': 'Purple',
            'a495bb50c5b14b44b5121370f02d74de': 'Orange',
            'a495bb60c5b14b44b5121370f02d74de': 'Blue',
            'a495bb70c5b14b44b5121370f02d74de': 'Yellow',
            'a495bb80c5b14b44b5121370f02d74de': 'Pink'
        }.get(uuid)

    # Convert Temp in F to C
    def convertFtoC(self, temperatureF):
        return (temperatureF - 32) * 5.0 / 9

    # Convert Tilt SG to float
    def convertSG(self, gravity):
        return float(gravity) / 1000

    # Store function
    def storeValue(self, colour, temperature, gravity):
        # This function is replaced under Fermentrack (just so we can override the class being used)
        tiltHydrometer = self.tiltHydrometers.get(colour)
        if (tiltHydrometer is None):
            tiltHydrometer = TiltHydrometer(colour, self.averagingPeriod, self.medianWindow, self.debug)
            self.tiltHydrometers[colour] = tiltHydrometer

        tiltHydrometer.setValues(temperature, gravity)

    # Retrieve function.
    def getValue(self, colour):
        returnValue = None
        tiltHydrometer = self.tiltHydrometers.get(colour)
        if (tiltHydrometer is not None):
            returnValue = tiltHydrometer.getValues()
        return returnValue

    # Scanner function
    def scan(self):
        # Keep scanning until the manager is told to stop.
        while self.scanning:
            try:
                sock = bluez.hci_open_dev(self.dev_id)

            except (Exception) as e:
                print("ERROR: Accessing bluetooth device: " + e.message)
                sys.exit(1)

            blescan.hci_le_set_scan_parameters(sock)
            blescan.hci_enable_le_scan(sock)

            try:
                # Keep scanning until the manager is told to stop.
                while self.scanning:
                    self.processSocket(sock)

                    reloaded = self.reloadSettings()
                    if (reloaded):
                        break
            except (Exception) as e:
                print("ERROR: Accessing bluetooth device whilst scanning: " + e.message)
                print("Resetting Bluetooth device")

    # Processes Tilt BLE data from open socket.
    def processSocket(self, sock):
        returnedList = blescan.parse_events(sock, 10)

        for beacon in returnedList:
            beaconParts = beacon.split(",")

            # Resolve whether the received BLE event is for a Tilt Hydrometer by looking at the UUID.
            name = self.tiltHydrometerName(beaconParts[1])

            # If the event is for a Tilt Hydrometer , process the data
            if name is not None:
                if (self.debug):
                    print(name + " Tilt Device Found (UUID " + str(beaconParts[1]) + "): " + str(beaconParts))

                # Get the temperature and convert to C if needed.
                temperature = int(beaconParts[2])
                if not self.inFahrenheit:
                    temperature = self.convertFtoC(temperature)

                # Get the gravity.
                gravity = self.convertSG(beaconParts[3])

                # Store the retrieved values in the relevant Tilt Hydrometer object.
                self.storeValue(name, temperature, gravity)
            else:
                # Output what has been found.
                if (self.debug):
                    print("UNKNOWN BLE Device Found: " + str(beaconParts))

    # Stop Scanning function
    def stop(self):
        self.scanning = False

    # Start the scanning thread
    def start(self):
        self.scanning = True
        self.brewthread = thread.start_new_thread(self.scan, ())

    # Checks to see if the settings file has changed, then reloads the settings if it has. Returns True if the settings were reloaded.
    def reloadSettings(self):
        # This function is replaced under Fermentrack
        filename = "tiltHydrometer/settings.ini"
        reloadSettings = False

        # Only check every x seconds
        if ((int(time.time()) - self.lastCheckedTime) >= DATA_REFRESH_WINDOW):
            self.lastCheckedTime = int(time.time())

            # Check that file exists
            if (os.path.isfile(filename)):
                fileModificationTime = os.path.getmtime(filename)

                # Check file modification time against last loaded time.
                if (self.lastLoadTime < fileModificationTime):
                    # File has been modified since last load (or first load)
                    self.loadSettings(filename)
                    self.lastLoadTime = int(time.time())
                    reloadSettings = True

        return reloadSettings

    # Load Settings from config file, overriding values given at creation. This needs to be called before the start function is called.
    def loadSettings(self, filename):
        # This function is replaced under Fermentrack
        try:
            print("Loading settings from file: " + filename)

            config = ConfigParser.ConfigParser()
            config.read(filename)

            # Load config values
            self.inFahrenheit = config.getboolean("Manager", "FahrenheitTemperatures")
            self.dev_ID = config.getint("Manager", "DeviceID")
            self.averagingPeriod = config.getint("Manager", "AveragePeriodSeconds")
            self.medianWindow = config.getint("Manager", "MedianWindowVals")
            self.debug = config.getboolean("Manager", "Debug")

            # Reset store
            self.tiltHydrometers = {}


        except (Exception) as e:
            print("ERROR: Loading default settings file (tiltHydrometer/settings.ini): " + e.message)
