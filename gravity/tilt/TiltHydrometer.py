import datetime
from typing import List, Dict, TYPE_CHECKING

from collections import deque

from gravity.models import TiltConfiguration, GravityLogPoint, GravitySensor
# from asgiref.sync import sync_to_async


class TiltHydrometer(object):
    # These are all the UUIDs currently available as Tilt colors
    tilt_colors = {
        'Red':    "a495bb10-c5b1-4b44-b512-1370f02d74de",
        'Green':  "a495bb20-c5b1-4b44-b512-1370f02d74de",
        'Black':  "a495bb30-c5b1-4b44-b512-1370f02d74de",
        'Purple': "a495bb40-c5b1-4b44-b512-1370f02d74de",
        'Orange': "a495bb50-c5b1-4b44-b512-1370f02d74de",
        'Blue':   "a495bb60-c5b1-4b44-b512-1370f02d74de",
        'Yellow': "a495bb70-c5b1-4b44-b512-1370f02d74de",
        'Pink':   "a495bb80-c5b1-4b44-b512-1370f02d74de",
    }  # type: Dict[str, str]


    # color_lookup is created at first use in color_lookup
    color_lookup_table = {}  # type: Dict[str, str]
    color_lookup_table_no_dash = {}  # type: Dict[str, str]

    def __init__(self, color: str):
        self.color = color  # type: str

        # The smoothing_window is set in the TiltConfiguration object - just defaulting it here for now
        self.smoothing_window = 60  # type: int
        self.gravity_list = deque(maxlen=self.smoothing_window)  # type: deque[float]
        self.temp_list = deque(maxlen=self.smoothing_window)  # type: deque[int]

        self.last_value_received = datetime.datetime.now() - self._cache_expiry_seconds()  # type: datetime.datetime
        self.last_saved_value = datetime.datetime.now()  # type: datetime.datetime

        self.gravity = 0.0  # type: float
        self.raw_gravity = 0.0  # type: float
        # Note - temp is always in fahrenheit
        self.temp = 0  # type: int
        self.raw_temp = 0  # type: int
        self.rssi = 0  # type: int

        self.obj = None  # type: TiltConfiguration

        # Let's load the object from Fermentrack as part of the initialization
        self.load_obj_from_fermentrack()

        if self.obj is not None:
            self.temp_format = self.obj.sensor.temp_format
        else:
            self.temp_format = GravitySensor.TEMP_FAHRENHEIT  # Defaulting to Fahrenheit as that's what the Tilt sends

    def __str__(self):
        return self.color

    def _cache_expiry_seconds(self) -> datetime.timedelta:
        # Assume we get 1 out of every 4 readings
        return datetime.timedelta(seconds=(self.smoothing_window * 1.2 * 4))

    def _cache_expired(self) -> bool:
        if self.obj is not None:
            # The other condition we want to explicitly clear the cache is if the temp format has changed between what
            # was loaded from the sensor object & what we previously had cached when the object was loaded
            if self.temp_format != self.obj.sensor.temp_format:
                # Clear the cached temp/gravity values &
                self.temp_format = self.obj.sensor.temp_format  # Cache the new temp format
                return True

        return self.last_value_received <= datetime.datetime.now() - self._cache_expiry_seconds()

    def _add_to_list(self, gravity, temp):
        # This adds a gravity/temp value to the list for smoothing/averaging
        if self._cache_expired():
            # The cache expired (we lost contact with the Tilt for too long). Clear the lists.
            self.gravity_list.clear()
            self.temp_list.clear()

        # Thankfully, deque enforces queue length, so all we need to do is add the value
        self.last_value_received = datetime.datetime.now()
        self.gravity_list.append(gravity)
        self.temp_list.append(temp)

    def should_save(self) -> bool:
        if self.obj is None:
            return False

        return self.last_saved_value <= datetime.datetime.now() - datetime.timedelta(seconds=(self.obj.polling_frequency))

    # def process_ibeacon_info(self, ibeacon_info: IBeaconAdvertisement, rssi):
    #     self.raw_gravity = ibeacon_info.minor / 1000
    #     if self.obj is None:
    #         # If there is no TiltConfiguration object set, just use the raw gravity the Tilt provided
    #         self.gravity = self.raw_gravity
    #     else:
    #         # Otherwise, apply the calibration
    #         self.gravity = self.obj.apply_gravity_calibration(self.raw_gravity)
    #
    #     # Temps are always provided in degrees fahrenheit - Convert to Celsius if required
    #     # Note - convert_temp_to_sensor returns as a tuple (with units) - we only want the degrees not the units
    #     self.raw_temp, _ = self.obj.sensor.convert_temp_to_sensor_format(ibeacon_info.major,
    #                                                                      GravitySensor.TEMP_FAHRENHEIT)
    #     self.temp = self.raw_temp
    #     self.rssi = rssi
    #     self._add_to_list(self.gravity, self.temp)

    def process_decoded_values(self, sensor_gravity: int, sensor_temp: int, rssi):
        if sensor_temp >= 999:
            # For the latest Tilts, this is now actually a special code indicating that the gravity is the version info.
            # Regardless of whether or not we end up doing anything with that information, we definitely do not want to
            # add it to the list
            return

        self.raw_gravity = sensor_gravity / 1000
        if self.obj is None:
            # If there is no TiltConfiguration object set, just use the raw gravity the Tilt provided
            self.gravity = self.raw_gravity
            self.raw_temp = sensor_temp
        else:
            # Otherwise, apply the calibration
            self.gravity = self.obj.apply_gravity_calibration(self.raw_gravity)

            # Temps are always provided in degrees fahrenheit - Convert to Celsius if required
            # Note - convert_temp_to_sensor returns as a tuple (with units) - we only want the degrees not the units
            self.raw_temp, _ = self.obj.sensor.convert_temp_to_sensor_format(sensor_temp,
                                                                             GravitySensor.TEMP_FAHRENHEIT)
        self.temp = self.raw_temp
        self.rssi = rssi
        self._add_to_list(self.gravity, self.temp)

    def smoothed_gravity(self):
        # Return the average gravity in gravity_list
        if len(self.gravity_list) <= 0:
            return None

        grav_total = 0
        for grav in self.gravity_list:
            grav_total += grav
        return round(grav_total / len(self.gravity_list), 3)  # Average it out & round

    def smoothed_temp(self):
        # Return the average temp in temp_list
        if len(self.temp_list) <= 0:
            return None

        temp_total = 0
        for temp in self.temp_list:
            temp_total += temp
        return round(temp_total / len(self.temp_list), 3)  # Average it out & round

    @classmethod
    def color_lookup(cls, color):
        if len(cls.color_lookup_table) <= 0:
            cls.color_lookup_table = {cls.tilt_colors[x]: x for x in cls.tilt_colors}
        if len(cls.color_lookup_table_no_dash) <= 0:
            cls.color_lookup_table_no_dash = {cls.tilt_colors[x].replace("-",""): x for x in cls.tilt_colors}

        if color in cls.color_lookup_table:
            return cls.color_lookup_table[color]
        elif color in cls.color_lookup_table_no_dash:
            return cls.color_lookup_table_no_dash[color]
        else:
            return None

    def print_data(self):
        print("{} Tilt: {} ({}) / {} F".format(self.color, self.smoothed_gravity(), self.gravity, self.temp))

#    @sync_to_async
    def load_obj_from_fermentrack(self, obj: TiltConfiguration = None):
        if obj is None:
            # If we weren't handed the object itself, try to load it
            try:
                obj = TiltConfiguration.objects.get(color=self.color,
                                                    connection_type=TiltConfiguration.CONNECTION_BLUETOOTH)
            except:
                # TODO - Rewrite this slightly
                self.obj = None
                return False

        # If the smoothing window changed, just recreate the deque objects
        if obj.smoothing_window_vals != self.smoothing_window:
            self.smoothing_window = obj.smoothing_window_vals
            self.gravity_list = deque(maxlen=self.smoothing_window)
            self.temp_list = deque(maxlen=self.smoothing_window)

        self.obj = obj

#    @sync_to_async
    def save_value_to_fermentrack(self, verbose=False):
        if self.obj is None:
            # If we don't have a TiltConfiguration object loaded, we can't save the data point
            if verbose:
                print("{} Tilt: No object loaded for this color".format(self.color))
            return False

        if self._cache_expired():
            if verbose:
                print("{} Tilt: Cache is expired/No data available to save".format(self.color))
            return False

        if self.smoothed_gravity() is None or self.smoothed_temp() is None:
            if verbose:
                print("{} Tilt: No data available to save".format(self.color))
            return False

        # TODO - Test that temp_format actually works as intended here
        new_point = GravityLogPoint(
            gravity=self.smoothed_gravity(),
            gravity_latest=self.gravity,
            temp=self.smoothed_temp(),
            temp_latest=self.temp,
            temp_format=self.obj.sensor.temp_format,
            temp_is_estimate=False,
            associated_device=self.obj.sensor,
        )

        if self.obj.sensor.active_log is not None:
            new_point.associated_log = self.obj.sensor.active_log

        new_point.save()

        # Also, set/save the RSSI/Raw Temp/Raw Gravity so we can load it for debugging
        self.obj.rssi = self.rssi
        self.obj.raw_gravity = self.raw_gravity
        self.obj.raw_temp = self.raw_temp
        self.obj.save_extras_to_redis()

        self.last_saved_value = datetime.datetime.now()

        if verbose:
            print("{} Tilt: Logging {}".format(self.color, self.smoothed_gravity()))

        else:
            if verbose:
                print("No data received.")
