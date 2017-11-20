import threading
import functools


import os, sys


# For Fermentrack compatibility, try to load the Django includes. If we fail, keep running, just set djangoLoaded
# as false. If it turns out the user tried to launch with dblist/dbcfg, die with an error message.
# Load up the Django specific stuff
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# This is so Django knows where to find stuff.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fermentrack_django.settings")
sys.path.append(BASE_DIR)

# This is so my local_settings.py gets loaded.
os.chdir(BASE_DIR)

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()


import gravity.models

# Since this is designed to replace the base TiltHydrometer classes, let's import everything from the parent file
from TiltHydrometer import *


class TiltHydrometerFermentrack(TiltHydrometer):

    def __init__(self, colour, tilt_manager, averagingPeriod=0, medianWindow=0, debug=False):
        self.temp_initialized = False  # Adding this for Fermentrack
        self.gravity_initialized = False  # Adding this for Fermentrack

        # TiltManager is an instance of TiltHydrometerManagerFermentrack
        self.tilt_manager = tilt_manager
        self.colour = colour
        self.lock = threading.Lock()
        self.averagingPeriod = averagingPeriod
        self.medianWindow = medianWindow
        self.debug = debug
        self.values = []
        self.calibrationDataTime = {}
        self.calibrate()


    # Load the calibration settings from file and create the calibration functions
    def tiltHydrometerCalibrationFunction(self, type, colour):
        returnFunction = noCalibration

        originalValues = []
        actualValues = []

        if type == 'temperature':
            if self.temp_initialized:
                # Since we don't have a way currently to determine if new calibration data is available, assume there
                # is never any new data after initialization
                return None

            self.temp_initialized = True

            calibration_points = self.tilt_manager.obj.tilttempcalibrationpoint_set.all()

            for this_point in calibration_points:
                # For the temperature calibration points, we need to convert to the appropriate temperature format
                originalValues.append(this_point.actual_in_preferred_format())
                actualValues.append(this_point.actual_in_preferred_format())

        elif type == 'gravity':
            if self.gravity_initialized:
                # Since we don't have a way currently to determine if new calibration data is available, assume there
                # is never any new data after initialization
                return None

            self.gravity_initialized = True

            calibration_points = self.tilt_manager.obj.tiltgravitycalibrationpoint_set.all()

            for this_point in calibration_points:
                originalValues.append(this_point.orig_value)
                actualValues.append(this_point.actual_value)

        else:
            raise NotImplementedError

        # If more than two values, use interpolation
        if (len(actualValues) >= 2):
            interpolationFunction = interp1d(originalValues, actualValues, bounds_error=False, fill_value=1)
            returnFunction = functools.partial(extrapolationCalibration, extrap1d(interpolationFunction))
            # print "TiltHydrometer (" + colour + "): Initialised " + type.capitalize() + " Calibration: Interpolation"
        # Not enough values. Likely just an offset calculation
        elif (len(actualValues) == 1):
            offset = actualValues[0] - originalValues[0]
            returnFunction = functools.partial(offsetCalibration, offset)
            # print "TiltHydrometer (" + colour + "): Initialised " + type.capitalize() + " Calibration: Offset (" + str(
            #     offset) + ")"
        return returnFunction




class TiltHydrometerManagerFermentrack(TiltHydrometerManager):
    def __init__(self, device):
        self.initialized = False
        self.obj = device
        self.debug = False

        self.reloadSettings()

    # Checks to see if the settings file has changed, then reloads the settings if it has. Returns True if the settings were reloaded.
    def reloadSettings(self):
        if not self.initialized:
            self.loadSettings()
            self.initialized = True
            return True

        # If the reload flag is set (in redis) then we need to reload the settings.
        if self.obj.check_redis_reload_flag():
            self.loadSettings()
            self.obj.clear_redis_reload_flag()  # Clear the flag once reloaded
            return True
        else:
            return False

    def loadSettings(self, filename=""):  # Preserving the filename argument just in case something changes later on
        self.obj = gravity.models.TiltConfiguration.objects.get(color=self.obj.color)

        self.inFahrenheit = self.obj.inFahrenheit()
        self.dev_id = self.obj.dev_id()
        self.averagingPeriod = self.obj.average_period_secs
        self.medianWindow = self.obj.median_window_vals

        # Since we're now only managing a single Tilt per manager, reload the settings that would have been reloaded
        tiltHydrometer = self.tiltHydrometers.get(self.obj.color)
        if tiltHydrometer is not None:
            tiltHydrometer.averagingPeriod = self.averagingPeriod
            tiltHydrometer.medianWindow = self.medianWindow
            tiltHydrometer.temp_initialized = False  # This will force a reload
            tiltHydrometer.gravity_initialized = False  # This will force a reload


    # Store function
    def storeValue(self, colour, temperature, gravity):
        tiltHydrometer = self.tiltHydrometers.get(colour)
        if (tiltHydrometer is None):
            # TODO - Clean up the initialization function for TiltHydrometerFermentrack
            tiltHydrometer = TiltHydrometerFermentrack(colour, self, self.averagingPeriod, self.medianWindow, self.debug)
            self.tiltHydrometers[colour] = tiltHydrometer

        tiltHydrometer.setValues(temperature, gravity)
