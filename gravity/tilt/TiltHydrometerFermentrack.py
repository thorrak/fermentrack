# Since this is designed to replace the base TiltHydrometer classes, let's import everything from the parent file
from gravity.tilt.TiltHydrometer import *


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
            # print("TiltHydrometer (" + colour + "): Initialised " + type.capitalize() + " Calibration: Interpolation")
        # Not enough values. Likely just an offset calculation
        elif (len(actualValues) == 1):
            offset = actualValues[0] - originalValues[0]
            returnFunction = functools.partial(offsetCalibration, offset)
            # print("TiltHydrometer (" + colour + "): Initialised " + type.capitalize() + " Calibration: Offset (" + str(
            #     offset) + ")")
        return returnFunction

    def setValues(self, temperature, gravity):
        """Set/add the latest temperature & gravity readings to the store. These values will be calibrated before storing if calibration is enabled"""
        with self.lock:
            self.cleanValues()
            self.calibrate()

            # For temperature, use the old-style "calibration function" (even though this isn't supported in Fermentrack)
            # For gravity, use apply_gravity_calibration from the TiltConfiguration object
            calibratedTemperature = temperature
            calibratedGravity = self.tilt_manager.obj.apply_gravity_calibration(gravity)

            try:
                calibratedTemperature = self.tempCalibrationFunction(temperature)
            except (Exception) as e:
                print("ERROR: TiltHydrometer (" + self.colour + "): Unable to calibrate temperature: " + str(
                    temperature) + " - " + e.message)

            self.values.append(TiltHydrometerValue(calibratedTemperature, calibratedGravity))


class TiltHydrometerManagerFermentrack:
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

    obj = None

    def __init__(self, device):
        self.initialized = False
        self.obj = device
        self.debug = False

        self.reloadSettings()

    def loadSettings(self, filename=""):  # Preserving the filename argument just in case something changes later on
        self.obj = gravity.models.TiltConfiguration.objects.get(color=self.obj.color)

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



    # Store function
    def storeValue(self, colour, temperature, gravity):
        # TODO - COMPLETELY REWRITE THIS
        tiltHydrometer = self.tiltHydrometers.get(colour)
        if (tiltHydrometer is None):
            # TODO - Clean up the initialization function for TiltHydrometerFermentrack
            tiltHydrometer = TiltHydrometerFermentrack(colour, self, self.averagingPeriod, self.medianWindow, self.debug)
            self.tiltHydrometers[colour] = tiltHydrometer

        tiltHydrometer.setValues(temperature, gravity)

    # Convert Temp in F to C
    def convertFtoC(self, temperatureF):
        return (temperatureF - 32) * 5.0 / 9

    # Convert Tilt SG to float
    def convertSG(self, gravity):
        return float(gravity) / 1000

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
                    if reloaded:
                        break
            except (Exception) as e:
                print("ERROR: Accessing bluetooth device whilst scanning")
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
                if not self.obj.inFahrenheit:
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

