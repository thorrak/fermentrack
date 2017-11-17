import threading
import functools


import TiltHydrometer
import gravity.models

# To ease the overrides, going to import the appropriate functions directly
from TiltHydrometer import extrap1d, extrapolationCalibration, interp1d, offsetCalibration, noCalibration


class TiltHydrometerFermentrack(TiltHydrometer.TiltHydrometer):

    def __init__(self, colour, averagingPeriod=0, medianWindow=0, debug=False, tilt_manager = None):
        self.temp_initialized = False  # Adding this for Fermentrack
        self.gravity_initialized = False  # Adding this for Fermentrack

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

            calibration_points = self.tilt_manager.obj.tilttempcalibrationpoint_set()

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

            calibration_points = self.tilt_manager.obj.tiltgravitycalibrationpoint_set()

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




class TiltHydrometerManagerFermentrack(TiltHydrometer.TiltHydrometerManager):
    def __init__(self, device_id):
        self.initialized = False
        self.fermentrack_device_id = device_id
        self.obj = gravity.models.TiltConfiguration.objects.get(self.fermentrack_device_id)
        self.debug = False

        self.reloadSettings()

    # Checks to see if the settings file has changed, then reloads the settings if it has. Returns True if the settings were reloaded.
    def reloadSettings(self):
        if not self.initialized:
            self.loadSettings()
            self.initialized = True
            return True

        # TODO - Add a flag to trigger a reload from Redis or somewhere like that

        return False

    def loadSettings(self, filename=""):  # Preserving the filename argument just in case something changes later on
        self.obj = gravity.models.TiltConfiguration.objects.get(self.fermentrack_device_id)

        self.inFahrenheit = self.obj.inFahrenheit()
        self.dev_id = self.obj.dev_id()
        self.averagingPeriod = self.obj.average_period_secs
        self.medianWindow = self.obj.median_window_vals


    # Store function
    def storeValue(self, colour, temperature, gravity):
        tiltHydrometer = self.tiltHydrometers.get(colour)
        if (tiltHydrometer is None):
            # TODO - Clean up the initialization function for TiltHydrometerFermentrack
            tiltHydrometer = TiltHydrometerFermentrack(colour, self.averagingPeriod, self.medianWindow, self.debug, self)
            self.tiltHydrometers[colour] = tiltHydrometer

        tiltHydrometer.setValues(temperature, gravity)
