from __future__ import unicode_literals

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.db.models.signals import pre_delete
from django.dispatch import receiver

import os.path, csv, logging, socket
import json, time, datetime, pytz
from constance import config
from fermentrack_django import settings
import re

from . import udev_integration

from lib.ftcircus.client import CircusMgr, CircusException

logger = logging.getLogger(__name__)

# BrewPiDevice
# |
# |--Beer,Beer,...
# |  |
# |  |- BeerLog Point,Beer Log Point...
# |
# |--OldControlConstants/NewControlConstants
# |
# |--PinDevice,PinDevice...
#
# Fermentation Profile
# |
# |--FermentationProfilePoint,FermentationProfilePoint,...
#


class PinDevice(models.Model):
    class Meta:
        managed = False

    text = models.CharField(max_length=16, default="")
    type = models.CharField(max_length=8, default="")
    pin = models.IntegerField(default=-1)  # 'val' in the dict

    def __str__(self):
        return self.text

    # This factory method is used to allow us to quickly create an instance from a dict loaded in the firmware
    @classmethod
    def create_from_dict(cls, device_dict):
        # If the pin definition has " text" rather than "text" we assume the pin should be excluded
        if " text" in device_dict and "text" not in device_dict:
            return None
        new_device = cls(text=device_dict['text'], type=device_dict['type'], pin=device_dict['val'])
        return new_device

    # load_all_from_pinlist returns a list of available pin objects
    @classmethod
    def load_all_from_pinlist(cls, pinlist):
        all_pins = []

        for this_pin in pinlist:
            next_pin = cls.create_from_dict(this_pin)
            if next_pin is not None:
                all_pins.append(next_pin)

        return all_pins


# SensorDevice is a "sensor" (onewire addressable?) device
class SensorDevice(models.Model):
    class Meta:
        managed = False
        verbose_name = "Sensor Device"
        verbose_name_plural = "Sensor Devices"

    # DEVICE_NONE = 0, // End of chamber device list
    # DEVICE_CHAMBER_DOOR = 1, // switch sensor
    # DEVICE_CHAMBER_HEAT = 2,
    # DEVICE_CHAMBER_COOL = 3,
    # DEVICE_CHAMBER_LIGHT = 4, // actuator
    # DEVICE_CHAMBER_TEMP = 5,
    # DEVICE_CHAMBER_ROOM_TEMP = 6, // temp sensors
    # DEVICE_CHAMBER_FAN = 7, // a fan in the chamber
    # DEVICE_CHAMBER_RESERVED1 = 8, // reserved for future use
    #         // carboy devices
    # DEVICE_BEER_FIRST = 9,
    # DEVICE_BEER_TEMP = DEVICE_BEER_FIRST, // primary beer temp sensor
    # DEVICE_BEER_TEMP2 = 10, // secondary beer temp sensor
    # DEVICE_BEER_HEAT = 11, DEVICE_BEER_COOL = 12, // individual actuators
    # DEVICE_BEER_SG = 13, // SG sensor
    # DEVICE_BEER_RESERVED1 = 14, DEVICE_BEER_RESERVED2 = 15, // reserved
    # DEVICE_MAX = 16
    # };

    # Define the options for the choices below
    DEVICE_FUNCTION_NONE = 0
    DEVICE_FUNCTION_CHAMBER_DOOR = 1
    DEVICE_FUNCTION_CHAMBER_HEAT = 2
    DEVICE_FUNCTION_CHAMBER_COOL = 3
    DEVICE_FUNCTION_CHAMBER_LIGHT = 4
    DEVICE_FUNCTION_CHAMBER_TEMP = 5
    DEVICE_FUNCTION_CHAMBER_ROOM_TEMP = 6
    DEVICE_FUNCTION_CHAMBER_FAN = 7
    DEVICE_FUNCTION_MANUAL_ACTUATOR = 8
    DEVICE_FUNCTION_BEER_TEMP = 9
    DEVICE_FUNCTION_BEER_TEMP2 = 10
    DEVICE_FUNCTION_BEER_HEAT = 11
    DEVICE_FUNCTION_BEER_COOL = 12
    DEVICE_FUNCTION_BEER_SG = 13
    DEVICE_FUNCTION_BEER_RESERVED1 = 14
    DEVICE_FUNCTION_BEER_RESERVED2 = 15
    DEVICE_FUNCTION_MAX = 16

    INVERT_NOT_INVERTED = 0
    INVERT_INVERTED = 1


    DEVICE_FUNCTION_CHOICES = (
        (DEVICE_FUNCTION_NONE,          'NONE'),
        (DEVICE_FUNCTION_CHAMBER_DOOR,  'Chamber Door'),  # CHAMBER_DOOR
        (DEVICE_FUNCTION_CHAMBER_HEAT,  'Heating Relay'),  # CHAMBER_HEAT
        (DEVICE_FUNCTION_CHAMBER_COOL,  'Cooling Relay'),  # CHAMBER_COOL
        (DEVICE_FUNCTION_CHAMBER_LIGHT, 'Chamber Light'),  # CHAMBER_LIGHT
        (DEVICE_FUNCTION_CHAMBER_TEMP,  'Chamber Temp'),  # CHAMBER_TEMP
        (DEVICE_FUNCTION_CHAMBER_ROOM_TEMP, 'Room (outside) Temp'),  # CHAMBER_ROOM_TEMP
        (DEVICE_FUNCTION_CHAMBER_FAN,   'Chamber Fan'),  # CHAMBER_FAN
        # (DEVICE_FUNCTION_MANUAL_ACTUATOR, 'CHAMBER_RESERVED1'),   # Unused, reserved for future use - Tagged as "Manual Actuator" in develop www
        (DEVICE_FUNCTION_BEER_TEMP,     'Beer Temp'),           # Primary beer temp sensor
        # The rest of these are available in the code, but appear to have no implemented functionality.
        # Commenting them out for the time being.
        # (DEVICE_FUNCTION_BEER_TEMP2, 'BEER_TEMP2'),         # Secondary beer temp sensor (unimplemented)
        # (DEVICE_FUNCTION_BEER_HEAT, 'BEER_HEAT'),
        # (DEVICE_FUNCTION_BEER_COOL, 'BEER_COOL'),
        # (DEVICE_FUNCTION_BEER_SG, 'BEER_SG'),
        # (DEVICE_FUNCTION_BEER_RESERVED1, 'BEER_RESERVED1'),
        # (DEVICE_FUNCTION_BEER_RESERVED2, 'BEER_RESERVED2'),
        # (DEVICE_FUNCTION_MAX, 'MAX'),
    )

    # DEVICE_HARDWARE_NONE = 0,
    # DEVICE_HARDWARE_PIN = 1, // a digital pin, either input or output
    # DEVICE_HARDWARE_ONEWIRE_TEMP = 2, // a onewire temperature sensor
    # DEVICE_HARDWARE_ONEWIRE_2413 = 3 // a onewire 2 - channel PIO input or output.

    DEVICE_HARDWARE_CHOICES = (
        (0, 'NONE'),
        (1, 'PIN'),
        (2, 'ONEWIRE_TEMP'),
        (3, 'ONEWIRE_2413'),
        (4, 'ONEWIRE_2408/Valve'),
    )

    DEVICE_TYPE_CHOICES = (
        (0, 'None'),
        (1, 'Temp Sensor'),
        (2, 'Switch Sensor'),
        (3, 'Switch Actuator'),
        (4, 'PWM Actuator'),
        (5, 'Manual Actuator'),
    )

    INVERT_CHOICES = (
        (INVERT_NOT_INVERTED,   'Not Inverted'),
        (INVERT_INVERTED,       'Inverted'),
    )

    address = models.CharField(max_length=16, blank=True, default="")
    device_index = models.IntegerField(default=-1)
    type = models.IntegerField(default=0)
    chamber = models.IntegerField(default=0)
    beer = models.IntegerField(default=0)
    device_function = models.IntegerField(default=0, choices=DEVICE_FUNCTION_CHOICES)
    hardware = models.IntegerField(default=2, choices=DEVICE_HARDWARE_CHOICES)
    deactivated = models.IntegerField(default=0)
    pin = models.IntegerField(default=0)
    calibrate_adjust = models.FloatField(default=0.0)
    pio = models.IntegerField(null=True, default=None)
    invert = models.IntegerField(default=1, choices=INVERT_CHOICES)
    sensor_value = models.FloatField(default=0.0)

    # For the two ForeignKey fields, due to the fact that managed=False, we don't want Django attempting to enforce
    # referential integrity when a controller/PinDevice is deleted as there is no database table to enforce upon.
    # (You'll get a 'no_such_table' error)
    pin_data = models.ForeignKey(PinDevice, null=True, blank=True, default=None, on_delete=models.DO_NOTHING)

    controller = models.ForeignKey('BrewPiDevice', null=True, default=None,  on_delete=models.DO_NOTHING)

    # Defining the name as something readable for debugging
    def __str__(self):
        if self.hardware == 1:
            return "Pin {}".format(self.pin)
        elif self.hardware == 2:
            return "TempSensor " + self.address
        elif self.hardware == 3:
            return "OneWire 2413 " + self.address
        elif self.hardware == 4:
            return "OneWire 2408 " + self.address


    # This factory method is used to allow us to quickly create an instance from a dict loaded from the firmware
    @classmethod
    def create_from_dict(cls, device_dict, pinlist_dict=None):
        new_device = cls()

        # An example string is as below (from one of my (unconfigured) onewire temperature sensors)
        # {u'a': u'28FF93A7A4150307', u'c': 1, u'b': 0, u'd': 0, u'f': 0, u'i': -1, u'h': 2, u'j': 0.0, u'p': 12, u't': 0}

        # and here is an example string from one of the 'pin' devices:
        # {u'c': 1, u'b': 0, u'd': 0, u'f': 0, u'i': -1, u'h': 1, u'p': 16, u't': 0, u'x': 1}

        # The following are defined in the code, but aren't interpreted here (for now)
        # const char DEVICE_ATTRIB_VALUE = 'v';		// print current values
        # const char DEVICE_ATTRIB_WRITE = 'w';		// write value to device

        if 'a' in device_dict:  # const char DEVICE_ATTRIB_ADDRESS = 'a';
            new_device.address = device_dict['a']

        if 'c' in device_dict:  # const char DEVICE_ATTRIB_CHAMBER = 'c';
            new_device.chamber = device_dict['c']

        if 'b' in device_dict:  # const char DEVICE_ATTRIB_BEER = 'b';
            new_device.beer = device_dict['b']

        if 'd' in device_dict:  # const char DEVICE_ATTRIB_DEACTIVATED = 'd';
            new_device.deactivated = device_dict['d']

        if 'f' in device_dict:  # const char DEVICE_ATTRIB_FUNCTION = 'f';
            new_device.device_function = device_dict['f']

        if 'i' in device_dict:  # const char DEVICE_ATTRIB_INDEX = 'i';
            new_device.device_index = device_dict['i']

        # Not allowing defaulting of new_device.hardware
        # if 'h' in device_dict:  # const char DEVICE_ATTRIB_HARDWARE = 'h';
        new_device.hardware = device_dict['h']

        if 'j' in device_dict:  # const char DEVICE_ATTRIB_CALIBRATEADJUST = 'j';	// value to add to temp sensors to bring to correct temperature
            new_device.calibrate_adjust = device_dict['j']

        #  TODO - Determine if I should error out if we don't receive 'p' back in the dict, or should allow defaulting
        if 'p' in device_dict:  # const char DEVICE_ATTRIB_PIN = 'p';
            new_device.pin = device_dict['p']

        #  TODO - Determine if I should error out if we don't receive 't' back in the dict, or should allow defaulting
        if 't' in device_dict:  # const char DEVICE_ATTRIB_TYPE = 't';
            new_device.type = device_dict['t']

        # pio is only set if BREWPI_DS2413 is enabled (OneWire actuator support)
        if 'n' in device_dict:  # const char DEVICE_ATTRIB_PIO = 'n';
            new_device.pio = device_dict['n']

        if 'x' in device_dict:  # const char DEVICE_ATTRIB_INVERT = 'x';
            new_device.invert = int(device_dict['x'])

        if 'v' in device_dict:  # Temperature value (if we read values when we queried devices from the controller)
            new_device.sensor_value = device_dict['v']

        if pinlist_dict:
            for this_pin in pinlist_dict:
                if this_pin.pin == new_device.pin:
                    new_device.pin_data = this_pin

        return new_device


    @classmethod
    def load_all_from_devicelist(cls, device_list, pinlist_dict=None, controller=None):
        all_devices = []

        for this_device in device_list:
            # This gets wrapped in a try/except block as if the controller returns a malformed device list (e.g. missing
            # one of the required parameters, like 'h') we want to skip it.
            try:
                next_device = cls.create_from_dict(this_device, pinlist_dict)
                next_device.controller = controller
                all_devices.append(next_device)
            except:
                pass

        return all_devices

    def get_next_available_device_index(self):
        try:
            if not self.controller:  # If we can't load the controller (it's optional, after all) return None
                return None
            if len(self.controller.installed_devices) == 0:
                return 0
        except:
            return None

        indices = {}

        for i in range(0,25):  # Prepopulate indices as false
            indices[i] = False
        for this_device in self.controller.installed_devices:  # Iterate over installed_devices & update indices
            indices[this_device.device_index] = True
        for key in indices:  # Find the first unused index
            if not indices[key]:
                return key  # ...and return it
        return None  # If we used all indices, return None


    def set_defaults_for_device_function(self):
        # In the current state of the BrewPi firmware, a number of options that are available on the controller are
        # either confusing or unnecessary. Rather than force the user to figure them out, let's default them.

        # Device index is what is used internally by the BrewPi firmware to track installed devices. Once a device
        # is on the "installed" list, we need to always address it by the index. If it doesn't have an index assigned
        # yet, however, then we need to get the next available one and use it.
        if self.device_index < 0:
            self.device_index = self.get_next_available_device_index()

        if self.device_function > 0:  # If the device has a function, set the default chamber/beer
            # For the ESP8266 implementation, this same logic is enforced on the controller, as well
            self.chamber = 1  # Default the chamber to 1
            self.beer = 0  # Default the beer to 0
            if self.device_function >= 9 and self.device_function <=15:
                self.beer = 1  # ...unless this is an actual beer device, in which case default the beer to 1


    # This uses the "updateDevice" message. There is also a "writeDevice" message which is used to -create- devices.
    # (Used for "manual" actuators, aka buttons)
    def write_config_to_controller(self, uninstall=False):
        self.set_defaults_for_device_function()  # Bring the configuration to a consistent state

        # U:{"i":"0","c":"1","b":"0","f":"5","h":"2","p":"12","a":"28FF93A7A4150307"}
        config_dict = {}

        # The following options are universal for all hardware types
        config_dict['i'] = self.device_index
        config_dict['c'] = self.chamber
        config_dict['b'] = self.beer
        config_dict['f'] = self.device_function
        config_dict['h'] = self.hardware
        config_dict['p'] = self.pin
        # config_dict['d'] = self.deactivated

        if self.hardware == 1:  # Set options that are specific to pin devices
            config_dict['x'] = self.invert
        elif self.hardware == 2:  # Set options that are specific to OneWire temp sensors
            config_dict['j'] = self.calibrate_adjust
            config_dict['a'] = self.address


        sent_message = self.controller.send_message("applyDevice", json.dumps(config_dict))
        time.sleep(3)  # There's a 2.5 second delay in re-reading values within BrewPi Script - We'll give it 0.5s more

        self.controller.load_sensors_from_device()
        try:
            updated_device = SensorDevice.find_device_from_address_or_pin(self.controller.installed_devices, address=self.address, pin=self.pin)
        except ValueError:
            if uninstall:
                # If we were -trying- to uninstall the device, it's a good thing it doesn't show up in installed_devices
                return True
            else:
                return False

        if updated_device.device_index != self.device_index:
            return False
        elif updated_device.chamber != self.chamber:
            return False
        elif updated_device.beer != self.beer:
            return False
        elif updated_device.device_function != self.device_function:
            return False
        elif updated_device.hardware != self.hardware:
            return False
        elif updated_device.pin != self.pin:
            return False
        elif self.hardware == 1 and updated_device.invert != int(self.invert):
            return False
        elif self.hardware == 2 and updated_device.address != self.address:
            return False
        else:
            return True

    # Uninstall basically just sets device_function to 0
    def uninstall(self):
        self.device_function = SensorDevice.DEVICE_FUNCTION_NONE
        # Technically, the next 2 are overwritten in write_config_to_controller, but explicitly breaking them out here
        self.chamber = 0
        self.beer = 0

        return self.write_config_to_controller(uninstall=True)

    @staticmethod
    def find_device_from_address_or_pin(device_list, address=None, pin=None):
        if device_list is None:
            raise ValueError('No sensors/pins are available for this device')

        if address is not None and len(address) > 0:
            for this_device in device_list:
                if this_device.address == address:
                    return this_device
            # We weren't able to find a device with that address
            raise ValueError('Unable to find address in device_list')
        elif pin is not None:
            for this_device in device_list:
                if this_device.pin == pin:
                    return this_device
            # We weren't able to find a device with that pin number
            raise ValueError('Unable to find pin in device_list')
        else:
            # We weren't passed an address or pin number
            raise ValueError('Neither address nor pin passed to function')



#{"beerName": "Sample Data", "tempFormat": "C", "profileName": "Sample Profile", "dateTimeFormat": "yy-mm-dd", "dateTimeFormatDisplay": "mm/dd/yy" }
class BrewPiDevice(models.Model):
    """
    BrewPiDevice is the rough equivalent to an individual installation of brewpi-www
    """

    class Meta:
        verbose_name = "BrewPi Device"
        verbose_name_plural = "BrewPi Devices"


    TEMP_FORMAT_CHOICES = (('C', 'Celsius'), ('F', 'Fahrenheit'))

    DATA_LOGGING_ACTIVE = 'active'
    DATA_LOGGING_PAUSED = 'paused'
    DATA_LOGGING_STOPPED = 'stopped'

    DATA_LOGGING_CHOICES = (
        (DATA_LOGGING_ACTIVE, 'Active'),
        (DATA_LOGGING_PAUSED, 'Paused'),
        (DATA_LOGGING_STOPPED, 'Stopped')
    )
    DATA_POINT_TIME_CHOICES = (
        (10, '10 Seconds'),
        (30, '30 Seconds'),
        (60, '1 Minute'),
        (60*2, '2 Minutes'),
        (60*5, '5 Minutes'),
        (60*10, '10 Minutes'),
        (60*30, '30 Minutes'),
        (60*60, '1 Hour'),
    )
    BOARD_TYPE_CHOICES = (
        ('uno', 'Arduino Uno (or compatible)'),
        ('esp8266', 'ESP8266'),
        ('leonardo', 'Arduino Leonardo'),
        ('core', 'Core'),
        ('photon', 'Photon'),
    )

    CONNECTION_SERIAL = 'serial'
    CONNECTION_WIFI = 'wifi'

    CONNECTION_TYPE_CHOICES = (
        (CONNECTION_SERIAL, 'Serial (Arduino and others)'),
        (CONNECTION_WIFI, 'WiFi (ESP8266)'),
    )

    STATUS_ACTIVE = 'active'
    STATUS_UNMANAGED = 'unmanaged'
    STATUS_DISABLED = 'disabled'
    STATUS_UPDATING = 'updating'

    STATUS_CHOICES = (
        (STATUS_ACTIVE, 'Active, Managed by Circus'),
        (STATUS_UNMANAGED, 'Active, NOT managed by Circus'),
        (STATUS_DISABLED, 'Explicitly disabled, cannot be launched'),
        (STATUS_UPDATING, 'Disabled, pending an update'),
    )

    device_name = models.CharField(max_length=48, help_text="Unique name for this device", unique=True)

    # This is set at the device level, and should probably be read from the device as well. Going to include here
    # to cache it.
    temp_format = models.CharField(max_length=1, choices=TEMP_FORMAT_CHOICES, default='C', help_text="Temperature units")

    data_point_log_interval = models.IntegerField(default=30, choices=DATA_POINT_TIME_CHOICES,
                                                  help_text="Time between logged data points")

    ######## The following are used if we are loading the configuration directly from the database.
    useInetSocket = models.BooleanField(default=False, help_text="Whether or not to use an internet socket (rather than local)")
    socketPort = models.IntegerField(default=2222, validators=[MinValueValidator(10,"Port must be 10 or higher"),
                                                               MaxValueValidator(65535, "Port must be 65535 or lower")],
                                     help_text="The internet socket to use (only used if useInetSocket above is "
                                               "\"True\")")
    socketHost = models.CharField(max_length=128, default="localhost", help_text="The interface to bind for the "
                                                                                 "internet socket (only used if "
                                                                                 "useInetSocket above is \"True\")")
    # Note - Although we can manage logging_status from within Fermentrack, it's intended to be managed via
    # brewpi-script.
    logging_status = models.CharField(max_length=10, choices=DATA_LOGGING_CHOICES, default='stopped', help_text="Data logging status")

    serial_port = models.CharField(max_length=255, help_text="Serial port to which the BrewPi device is connected",
                                   default="auto")
    serial_alt_port = models.CharField(max_length=255, help_text="Alternate serial port to which the BrewPi device is connected (??)",
                                   default="None")

    udev_serial_number = models.CharField(max_length=255, blank=True,
                                          help_text="USB Serial ID number for autodetection of serial port", default="")

    prefer_connecting_via_udev = models.BooleanField(default=True, help_text="Prefer to connect to the device with the correct serial number instead of the serial_port")

    board_type = models.CharField(max_length=10, default="uno", choices=BOARD_TYPE_CHOICES, help_text="Board type to which BrewPi is connected")


    # Replaces the 'do not run' file used by brewpi-script
    status = models.CharField(max_length=15, default=STATUS_ACTIVE, choices=STATUS_CHOICES)

    socket_name = models.CharField(max_length=25, default="BEERSOCKET",
                                   help_text="Name of the file-based socket (Only used if useInetSocket is False)")

    connection_type = models.CharField(max_length=15, default='serial', choices=CONNECTION_TYPE_CHOICES,
                                       help_text="Type of connection between the Raspberry Pi and the hardware")
    wifi_host = models.CharField(max_length=40, default='None',
                                 help_text="mDNS host name or IP address for WiFi connected hardware (only used if " +
                                           "connection_type is wifi)")
    wifi_host_ip = models.CharField(max_length=46, default='', help_text="Cached IP address in case of mDNS issues (only used if connection_type is wifi)")
    wifi_port = models.IntegerField(default=23, validators=[MinValueValidator(10,"Port must be 10 or higher"),
                                                            MaxValueValidator(65535, "Port must be 65535 or lower")],
                                    help_text="The internet socket to use (only used if connection_type is wifi)")

    # The beer that is currently active & being logged
    active_beer = models.ForeignKey('Beer', null=True, blank=True, default=None, on_delete=models.SET_NULL)

    # The active fermentation profile (if any!)
    active_profile = models.ForeignKey('FermentationProfile', null=True, blank=True, default=None, on_delete=models.SET_NULL)

    # The time the fermentation profile was applied (all our math is based on this)
    time_profile_started = models.DateTimeField(null=True, blank=True, default=None)

    def is_temp_controller(self):  # This is a hack used in the site template so we can display relevant functionality
        return True

    def get_profile_temp(self):
        # If the object is inconsistent, don't return anything
        if self.active_profile is None:
            return None
        if self.time_profile_started is None:
            return None

        # self.sync_temp_format()  # Before we update the profile temp, make sure our math is consistent
        return self.active_profile.profile_temp(self.time_profile_started, self.temp_format)

    def is_past_end_of_profile(self):
        if self.active_profile is None:
            return None
        if self.time_profile_started is None:
            return None

        # self.sync_temp_format()  # Before we update the profile temp, make sure our math is consistent
        return self.active_profile.past_end_of_profile(self.time_profile_started)

    # Other things that aren't persisted in the database
    # available_devices = []
    # installed_devices = []
    # devices_are_loaded = False

    def __str__(self):
        # TODO - Make this test if the name is unicode, and return a default name if that is the case
        return self.device_name

    def __unicode__(self):
        return self.device_name
    
    
    def read_lcd_from_device(self):
        pass

    def get_active_beer_name(self):
        if self.active_beer:
            return self.active_beer.name
        else:
            return ""


    # I'm torn as to whether or not to move all of this out to another class. Leaving everything socket-related here
    # for now.
    def open_socket(self):
        if self.useInetSocket:
            this_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.SOL_TCP)
        else:
            this_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

        if this_socket:
            try:
                if self.useInetSocket:
                    this_socket.connect((self.socketHost, self.socketPort))
                else:
                    this_socket.connect(self.socket_name)
            except:
                this_socket.close()

        return this_socket

    @staticmethod
    def write_to_socket(this_socket, message):
        try:
            # Python 3 readiness
            encoded_message=message.encode(encoding="cp437")
            this_socket.sendall(encoded_message)
            return True
        except:
            return False

    @staticmethod
    def read_from_socket(this_socket):
        try:
            encoded_message = this_socket.recv(65536)
            return encoded_message.decode(encoding="cp437")
        except:
            return None

    def send_message(self, message, message_extended=None, read_response=False):
        message_to_send = message
        if message_extended is not None:
            message_to_send += "=" + message_extended
        this_socket = self.open_socket()
        if this_socket:
            if self.write_to_socket(this_socket, message_to_send):
                if read_response:
                    return self.read_from_socket(this_socket)
                else:
                    return True
        return False

    def read_lcd(self):
        try:
            lcd_text = json.loads(self.send_message("lcd", read_response=True))
        except:
            lcd_text = ["Cannot receive", "LCD text from", "Controller/Script"]


        # Due to the various codepage swaps, we're now receiving the raw degree symbol (0xB0) back when we poll the
        # LCD under Python 3. Let's replace it with "&deg;" for display in HTML
        deg_symbol = bytes([0xB0]).decode(encoding="cp437")
        sanitized_text = [n.replace(deg_symbol, "&deg;") for n in lcd_text]

        return sanitized_text

    def is_connected(self):
        # Tests if we're connected to the device via BrewPi-Script
        try:
            _ = json.loads(self.send_message("lcd", read_response=True))
        except:
            return False
        return True

    def retrieve_version(self):
        try:
            version_data = json.loads(self.send_message("getVersion", read_response=True))
        except:
            return None
        return version_data

    def is_legacy(self, version=None):
        if version == None:
            version = self.retrieve_version()
            if not version:
                # If we weren't passed a version & can't load from the device itself, return None
                return None  # There's probably a better way of doing this.

        if version['version'][:3] == "0.2":
            return True
        return False

    def retrieve_control_constants(self):
        version = self.retrieve_version()
        if version:
            if self.is_legacy(version):
                # If we're dealing with a legacy controller, we need to work with the old control constants.
                control_constants = OldControlConstants()
                control_constants.load_from_controller(self)
            else:
                # Otherwise, we need to work with the NEW control constants
                control_constants = NewControlConstants()
                control_constants.load_from_controller(self)

            # Returning both the control constants structure as well as which structure we ended up using
            control_constants.controller = self
            return control_constants, self.is_legacy(version=version)
        return None, None

    def request_device_refresh(self):
        self.send_message("refreshDeviceList")  # refreshDeviceList refreshes the cache within brewpi-script
        time.sleep(0.1)

    # We don't persist the "sensor" (onewire/pin) list in the database, so we always have to load it from the
    # controller
    def load_sensors_from_device(self):
        # Note - getDeviceList actually is reading the cache from brewpi-script - not the firmware itself
        loop_number = 1
        device_response = self.send_message("getDeviceList", read_response=True)

        # If the cache wasn't up to date, request that brewpi-script refresh it
        if device_response == "device-list-not-up-to-date":
            self.request_device_refresh()

        # This can take a few seconds. Periodically poll brewpi-script to try to get a response.
        while device_response == "device-list-not-up-to-date" and loop_number <= 4:
            time.sleep(5)
            device_response = self.send_message("getDeviceList", read_response=True)
            loop_number += 1

        if not device_response or device_response == "device-list-not-up-to-date":
            self.all_pins = None
            self.available_devices = None
            self.installed_devices = None
            if not device_response:
                # We weren't able to reach brewpi-script
                self.error_message = "Unable to reach brewpi-script. Try restarting brewpi-script."
            else:
                # We were able to reach brewpi-script, but it wasn't able to reach the controller
                self.error_message = "BrewPi-script wasn't able to load sensors from the controller. "
                self.error_message += "Try restarting brewpi-script. If that fails, try restarting the controller."
            return False  # False

        # Devices loaded
        devices = json.loads(device_response)
        self.all_pins = PinDevice.load_all_from_pinlist(devices['pinList'])
        self.available_devices = SensorDevice.load_all_from_devicelist(devices['deviceList']['available'], self.all_pins, self)
        self.installed_devices = SensorDevice.load_all_from_devicelist(devices['deviceList']['installed'], self.all_pins, self)

        # Loop through the installed devices to set up the special links to the key ones
        for this_device in self.installed_devices:
            if this_device.device_function == SensorDevice.DEVICE_FUNCTION_CHAMBER_DOOR:  # (1, 'CHAMBER_DOOR'),
                self.door_pin = this_device
            elif this_device.device_function == SensorDevice.DEVICE_FUNCTION_CHAMBER_HEAT:  # (2, 'CHAMBER_HEAT'),
                self.heat_pin = this_device
            elif this_device.device_function == SensorDevice.DEVICE_FUNCTION_CHAMBER_COOL:  # (3, 'CHAMBER_COOL'),
                self.cool_pin = this_device
            elif this_device.device_function == SensorDevice.DEVICE_FUNCTION_CHAMBER_TEMP:  # (5, 'CHAMBER_TEMP'),
                self.chamber_sensor = this_device
            elif this_device.device_function == SensorDevice.DEVICE_FUNCTION_CHAMBER_ROOM_TEMP:  # (6, 'CHAMBER_ROOM_TEMP'),
                self.room_sensor = this_device
            elif this_device.device_function == SensorDevice.DEVICE_FUNCTION_BEER_TEMP:  # (9, 'BEER_TEMP'),
                self.beer_sensor = this_device

        return True

    # TODO - Determine if we care about controlSettings
    # # Retrieve the control settings from the controller
    # def retrieve_control_settings(self):
    #     version = self.retrieve_version()
    #     if version:
    #         if self.is_legacy(version):
    #             # If we're dealing with a legacy controller, we need to work with the old control constants.
    #             control_settings = OldControlSettings()
    #             control_settings.load_from_controller(self)
    #         else:
    #             # Otherwise, we need to work with the NEW control constants
    #             control_settings = OldControlSettings()
    #             control_settings.load_from_controller(self)
    #
    #         # Returning both the control constants structure as well as which structure we ended up using
    #         control_settings.controller = self
    #         return control_settings, self.is_legacy(version=version)
    #     return None, None

    def sync_temp_format(self) -> bool:
        # This queries the controller to see if we have the correct tempFormat set (If it matches what is specified
        # in the device definition above). If it doesn't, we overwrite what is on the device to match what is in the
        # device definition.
        control_constants, legacy_mode = self.retrieve_control_constants()

        if control_constants is None:
            return False

        if control_constants.tempFormat != self.temp_format:  # The device has the wrong tempFormat - We need to update
            control_constants.tempFormat = self.temp_format

            if legacy_mode:
                if self.temp_format == 'C':
                    control_constants.tempSetMax = 35.0
                    control_constants.tempSetMin = -8.0
                elif self.temp_format == 'F':
                    control_constants.tempSetMax = 90.0
                    control_constants.tempSetMin = 20.0
                else:
                    return False  # If we can't define a good max/min, don't do anything
            else:
                # TODO - Fix/expand this when we add "modern" controller support
                return False

            control_constants.save_to_controller(self, "tempFormat")

            if legacy_mode:
                control_constants.save_to_controller(self, "tempSetMax")
                control_constants.save_to_controller(self, "tempSetMin")

            return True
        return False

    def get_temp_control_status(self):
        device_mode = self.send_message("getMode", read_response=True)

        control_status = {}
        if (device_mode is None) or (not device_mode):  # We were unable to read from the device
            control_status['device_mode'] = "unable_to_connect"  # Not sure if I want to pass the message back this way
            return control_status

        # If we could connect to the device, force-sync the temp format
        self.sync_temp_format()

        if device_mode == 'o':  # Device mode is off
            control_status['device_mode'] = "off"

        elif device_mode == 'b':  # Device mode is beer constant
            control_status['device_mode'] = "beer_constant"
            control_status['set_temp'] = self.send_message("getBeer", read_response=True)

        elif device_mode == 'f':  # Device mode is fridge constant
            control_status['device_mode'] = "fridge_constant"
            control_status['set_temp'] = self.send_message("getFridge", read_response=True)

        elif device_mode == 'p':  # Device mode is beer profile
            control_status['device_mode'] = "beer_profile"

        else:
            # No idea what the device mode is
            logger.error("Invalid device mode '{}'".format(device_mode))

        return control_status

    def reset_profile(self):
        if self.active_profile is not None:
            self.active_profile = None
        if self.time_profile_started is not None:
            self.time_profile_started = None
        self.save()

    def set_temp_control(self, method, set_temp=None, profile=None, profile_startat=None):
        if method == "off":
            self.reset_profile()
            self.send_message("setOff")
        elif method == "beer_constant":
            if set_temp is not None:
                self.reset_profile()
                self.send_message("setBeer", str(set_temp))
            else:
                error_message = "Device {} set to beer_constant without a setpoint".format(self.device_name)
                logger.error(error_message)
                raise ValueError(error_message)
        elif method == "fridge_constant":
            if set_temp is not None:
                self.reset_profile()
                self.send_message("setFridge", str(set_temp))
            else:
                error_message = "Device {} set to fridge_constant without a setpoint".format(self.device_name)
                logger.error(error_message)
                raise ValueError(error_message)
        elif method == "beer_profile":
            try:
                ferm_profile = FermentationProfile.objects.get(id=profile)
            except:
                error_message ="Device {} set to beer_profile {} but the profile could not be located".format(
                    self.device_name, profile)
                logger.error(error_message)
                raise ValueError(error_message)

            if not ferm_profile.is_assignable():
                error_message = "Device {} set to beer_profile {} but the profile isn't assignable".format(
                    self.device_name, profile)
                logger.error(error_message)
                raise ValueError(error_message)

            if profile_startat is not None:
                start_at = profile_startat
            else:
                start_at = datetime.timedelta(seconds=0)  # Set start_at to have no effect

            self.active_profile = ferm_profile

            timezone_obj = pytz.timezone(getattr(settings, 'TIME_ZONE', 'UTC'))
            # We're subtracting start_at because we want to start in the past
            self.time_profile_started = timezone.now() - start_at

            self.save()

            self.send_message("setActiveProfile", str(self.active_profile.id))

        return True  # If we made it here, return True (we did our job)

    def start_new_brew(self, beer_name=None):
        if beer_name is None:
            if self.active_beer:
                beer_name = self.active_beer.name
            else:
                return False
        response = self.send_message("startNewBrew", message_extended=beer_name, read_response=True)
        return response

    def manage_logging(self, status):
        if status == 'stop':
            # This will be repeated by brewpi.py, but doing it here so we get up-to-date display in the dashboard
            if hasattr(self, 'gravity_sensor') and self.gravity_sensor is not None:
                # If there is a linked gravity log, stop that as well
                self.gravity_sensor.active_log = None
                self.gravity_sensor.save()
            self.active_beer = None
            self.save()
            response = self.send_message("stopLogging", read_response=True)
        elif status == 'resume':
            response = self.send_message("resumeLogging", read_response=True)
        elif status == 'pause':
            response = self.send_message("pauseLogging", read_response=True)
        else:
            response = '{"status": 1, "statusMessage": "Invalid logging request"}'
        if not response:
            response = '{"status": 1, "statusMessage": "Unable to contact brewpi-script for this controller"}'
        return json.loads(response)

    def reset_eeprom(self):
        response = self.send_message("resetController") # Reset the controller
        time.sleep(1)                                   # Give it 1 second to complete
        synced = self.sync_temp_format()                # ...then resync the temp format
        return synced

    def reset_wifi(self) -> bool:
        response = self.send_message("resetWiFi") # Reset the controller WiFi settings
        time.sleep(1)                                   # Give it 1 second to complete
        return True

    def restart(self) -> bool:
        response = self.send_message("restartController") # Restart the controller
        time.sleep(1)                                   # Give it 1 second to complete
        return True

    def get_control_constants(self):
        return json.loads(self.send_message("getControlConstants", read_response=True))

    def set_parameters(self, parameters):
        return self.send_message("setParameters", json.dumps(parameters))

    def get_dashpanel_info(self):
        try:  # This is apparently failing when being called in a loop for external_push - Wrapping in a try/except so the loop doesn't die
            return json.loads(self.send_message("getDashInfo", read_response=True))
        except TypeError:
            return None

    def circus_parameter(self) -> int:
        """Returns the parameter used by Circus to track this device's processes"""
        return self.id

    def start_process(self):
        """Start this device process, raises CircusException if error"""
        fc = CircusMgr()
        circus_process_name = u"dev-{}".format(self.circus_parameter())
        fc.start(name=circus_process_name)

    def remove_process(self):
        """Remove this device process, raises CircusException if error"""
        fc = CircusMgr()
        circus_process_name = u"dev-{}".format(self.circus_parameter())
        fc.remove(name=circus_process_name)

    def stop_process(self):
        """Stop this device process, raises CircusException if error"""
        fc = CircusMgr()
        circus_process_name = u"dev-{}".format(self.circus_parameter())
        fc.stop(name=circus_process_name)

    def restart_process(self):
        """Restart the deviece process, raises CircusException if error"""
        fc = CircusMgr()
        circus_process_name = u"dev-{}".format(self.circus_parameter())
        fc.restart(name=circus_process_name)

    def status_process(self):
        """Status this device process, raises CircusException if error"""
        fc = CircusMgr()
        circus_process_name = u"dev-{}".format(self.circus_parameter())
        status = fc.application_status(name=circus_process_name)
        return status

    def get_cached_ip(self, save_to_cache=True):
        # I really hate the name of the function, but I can't think of anything else. This basically does three things:
        # 1. Looks up the mDNS hostname (if any) set as self.wifi_host and gets the IP address
        # 2. (Optional) Saves that IP address to self.wifi_host_ip (if we were successful in step 1)
        # 3. Returns the found IP address (if step 1 was successful), the cached (self.wifi_host_ip) address if it
        #    wasn't, or 'None' if we don't have a cached address and we weren't able to resolve the hostname
        if len(self.wifi_host) > 4:
            try:
                ip_list = []
                ais = socket.getaddrinfo(self.wifi_host, 0, 0, 0, 0)
                for result in ais:
                    ip_list.append(result[-1][0])
                ip_list = list(set(ip_list))
                resolved_address = ip_list[0]
                if self.wifi_host_ip != resolved_address and save_to_cache:
                    # If we were able to find an IP address, save it to the cache
                    self.wifi_host_ip = resolved_address
                    self.save()
                return resolved_address
            except:
                # TODO - Add an error message here
                if len(self.wifi_host_ip) > 6:
                    # We weren't able to resolve the hostname (self.wifi_host) but we DID have a cached IP address.
                    # Return that.
                    return self.wifi_host_ip
                else:
                    return None
        # In case of error (or we have no wifi_host)
        return None

    def get_port_from_udev(self):
        # get_port_from_udev() looks for a USB device connected which matches self.udev_serial_number. If one is found,
        # it returns the associated device port. If one isn't found, it returns None (to prevent the cached port from
        # being used, and potentially pointing to another, unrelated device)

        if self.connection_type != self.CONNECTION_SERIAL:
            return self.serial_port  # If we're connecting via WiFi, don't attempt autodetection

        # If the user elected to not use udev to get the port, just return self.serial_port
        if not self.prefer_connecting_via_udev:
            return self.serial_port

        # If the platform doesn't support udev (isn't Linux) then return self.serial_port as well.
        if not udev_integration.valid_platform_for_udev():
            return self.serial_port

        # TODO - Detect if this is a Fuscus board and return self.serial_port (as well as setting prefer_connecting_via_udev)

        # If the udev_serial_number isn't yet set, try setting it
        if self.udev_serial_number == "":
            if not self.set_udev_from_port():
                # If we can't set it (device isn't connected, etc.) then return None
                return None

        udev_node = udev_integration.get_node_from_serial(self.udev_serial_number)

        if udev_node is not None:
            # The udev lookup found a device! Return the appropriate serial port.
            if self.serial_port != udev_node:
                # If the serial port changed, cache it.
                self.serial_port = udev_node
                self.save()
            return udev_node
        else:
            # The udev lookup failed - return None
            return None

    def set_udev_from_port(self):
        # set_udev_from_port() quickly scans the device connected at self.serial_port and - if found - saves the
        # associated udev serial number to the object.
        udev_serial_number = udev_integration.get_serial_from_node(self.serial_port)

        if udev_serial_number is not None:
            self.udev_serial_number = udev_serial_number
            self.save()
            return True

        # We failed to look up the udev serial number.
        return False


class Beer(models.Model):
    # Beers are unique based on the combination of their name & the original device
    name = models.CharField(max_length=255, db_index=True,
                            help_text='Name of the beer being logged (must be unique)')
    device = models.ForeignKey(BrewPiDevice, db_index=True, on_delete=models.SET_NULL, null=True,
                               help_text='The linked temperature control device from which data is logged')
    created = models.DateTimeField(default=timezone.now, help_text='When the beer log was initially created')

    # format generally should be equal to device.temp_format. We're caching it here specifically so that if the user
    # updates the device temp format somehow we will continue to log in the OLD format. We'll need to make a giant
    # button that allows the user to convert the log files to the new format if they're different.
    format = models.CharField(max_length=1, default='F', help_text='Temperature format to write the logs in')

    # model_version is the revision number of the "Beer" and "BeerLogPoint" models, designed to be iterated when any
    # change is made to the format/content of the flatfiles that would be written out. The idea is that a separate
    # converter could then be written moving between each iteration of model_version that could then be sequentially
    # applied to bring a beer log in line with what the model then expects.

    # Version 1: Original version
    # Version 2: Adds 'state' to 'base_csv' for state plotting
    model_version = models.IntegerField(default=2, help_text='Version # used for the logged file format')

    gravity_enabled = models.BooleanField(default=False, help_text='Is gravity logging enabled for this beer log?')

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.__str__()

    def column_headers(self, which='base_csv', human_readable=False):
        if which == 'base_csv':
            if human_readable:
                headers = ['Log Time', 'Beer Temp', 'Beer Setting', 'Fridge Temp', 'Fridge Setting', 'Room Temp']
            else:
                headers = ['log_time', 'beer_temp', 'beer_set', 'fridge_temp', 'fridge_set', 'room_temp']

        elif which == 'full_csv':
            if human_readable:
                # Currently unused
                headers = ['log_time', 'beer_temp', 'beer_set', 'beer_ann', 'fridge_temp', 'fridge_set', 'fridge_ann',
                           'room_temp', 'state', 'temp_format', 'associated_beer_id']
            else:
                headers = ['log_time', 'beer_temp', 'beer_set', 'beer_ann', 'fridge_temp', 'fridge_set', 'fridge_ann',
                           'room_temp', 'state', 'temp_format', 'associated_beer_id']
        else:
            return None

        # This works because we're appending the gravity data to both logs
        if self.gravity_enabled:
            if human_readable:
                headers.append('Gravity')
                headers.append('Gravity Sensor Temp')
            else:
                headers.append('gravity')
                headers.append('grav_temp')

        if which == 'base_csv' and self.model_version > 1:
            # For model versions 2 and greater, we are appending "state" to the base CSV.
            if human_readable:
                headers.append('State')  # I don't think this gets used anywhere...
            else:
                headers.append('state')

        return headers

    def base_column_visibility(self):
        # TODO - Determine if we want to take some kind of user setting into account (auto-hide room temp, for example)
        # headers = [x, 'beer_temp', 'beer_set', 'fridge_temp', 'fridge_set', 'room_temp']
        visibility = "[true, true, true, true, true"

        # This works because we're appending the gravity data to both logs
        if self.gravity_enabled:
            visibility += ", true, true"

        if self.model_version >= 1:
            visibility += ", false"  # Literally the whole point of this code block is to hide "state"

        visibility += "]"

        return visibility

    def column_headers_to_graph_string(self, which='base_csv'):
        col_headers = self.column_headers(which, True)

        graph_string = ""

        for this_header in col_headers:
            graph_string += "'" + this_header + "', "

        if graph_string.__len__() > 2:
            return graph_string[:-2]
        else:
            return ""

    @staticmethod
    def name_is_valid(proposed_name):
        # Since we're using self.name in a file path, want to make sure no injection-type attacks can occur.
        return True if re.match("^[a-zA-Z0-9 _-]*$", proposed_name) else False

    def base_filename(self):  # This is the "base" filename used in all the files saved out
        # Including the beer ID in the file name to ensure uniqueness (if the user duplicates the name, for example)
        if self.name_is_valid(self.name):
            return "Device " + str(self.device_id) + " - B" + str(self.id) + " - " + self.name
        else:
            return "Device " + str(self.device_id) + " - B" + str(self.id) + " - NAME ERROR - "

    def full_filename(self, which_file, extension_only=False):
        if extension_only:
            base_name = ""
        else:
            base_name = self.base_filename()

        if which_file == 'base_csv':
            return base_name + "_graph.csv"
        elif which_file == 'full_csv':
            return base_name + "_full.csv"
        elif which_file == 'annotation_json':
            return base_name + "_annotations.almost_json"
        else:
            return None

    def data_file_url(self, which_file):
        return settings.DATA_URL + self.full_filename(which_file, extension_only=False)

    def full_csv_url(self):
        return self.data_file_url('full_csv')

    def full_csv_exists(self) -> bool:
        # This is so that we can test if the log exists before presenting the user the option to download it
        file_name_base = os.path.join(settings.BASE_DIR, settings.DATA_ROOT, self.base_filename())
        full_csv_file = file_name_base + self.full_filename('full_csv', extension_only=True)
        return os.path.isfile(full_csv_file)

    def can_log_gravity(self):
        if self.gravity_enabled is False:
            return False
        if self.device.gravity_sensor is None:
            return False
        return True


    # def base_csv_url(self):
    #     return self.data_file_url('base_csv')

    # TODO - Add function to allow conversion of log files between temp formats


# When the user attempts to delete a beer, also delete the log files associated with it.
@receiver(pre_delete, sender=Beer)
def delete_beer(sender, instance, **kwargs):
    file_name_base = os.path.join(settings.BASE_DIR, settings.DATA_ROOT, instance.base_filename())

    base_csv_file = file_name_base + instance.full_filename('base_csv', extension_only=True)
    full_csv_file = file_name_base + instance.full_filename('full_csv', extension_only=True)
    annotation_json = file_name_base + instance.full_filename('annotation_json', extension_only=True)

    for this_filepath in [base_csv_file, full_csv_file, annotation_json]:
        try:
            os.remove(this_filepath)
        except OSError:
            pass



class BeerLogPoint(models.Model):
    """
    BeerLogPoint contains the individual temperature log points we're saving
    """

    class Meta:
        managed = False  # Since we're using flatfiles rather than a database
        verbose_name = "Beer Log Point"
        verbose_name_plural = "Beer Log Points"
        ordering = ['log_time']

    STATE_CHOICES = (
        (0, 'IDLE'),
        (1, 'STATE_OFF'),
        (2, 'DOOR_OPEN'),
        (3, 'HEATING'),
        (4, 'COOLING'),
        (5, 'WAITING_TO_COOL'),
        (6, 'WAITING_TO_HEAT'),
        (7, 'WAITING_FOR_PEAK_DETECT'),
        (8, 'COOLING_MIN_TIME'),
        (9, 'HEATING_MIN_TIME'),
    )
    TEMP_FORMAT_CHOICES = (('C', 'Celsius'), ('F', 'Fahrenheit'))


    beer_temp = models.DecimalField(max_digits=13, decimal_places=10, null=True)
    beer_set = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    beer_ann = models.CharField(max_length=255, null=True)

    fridge_temp = models.DecimalField(max_digits=13, decimal_places=10, null=True)
    fridge_set = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    fridge_ann = models.CharField(max_length=255, null=True)

    room_temp = models.DecimalField(max_digits=13, decimal_places=10, null=True)
    state = models.IntegerField(choices=STATE_CHOICES, default=0)
    log_time = models.DateTimeField(default=timezone.now, db_index=True)

    # Adding temp_format here so we can do conversions later on if we want to
    temp_format = models.CharField(max_length=1, choices=TEMP_FORMAT_CHOICES, default='C')

    associated_beer = models.ForeignKey(Beer, db_index=True, on_delete=models.DO_NOTHING)

    gravity = models.DecimalField(max_digits=5, decimal_places=3, null=True)
    gravity_temp = models.DecimalField(max_digits=13, decimal_places=10, null=True)


    def has_gravity_enabled(self):
        # Just punting this upstream
        if self.associated_beer_id is not None:
            return self.associated_beer.gravity_enabled
        else:
            return False

    def can_log_gravity(self):
        if self.associated_beer_id is not None:
            return self.associated_beer.can_log_gravity()
        else:
            return False

    def enrich_gravity_data(self):
        # enrich_graity_data is called to enrich this data point with the relevant gravity data
        # Only relevant if self.has_gravity_enabled is true (The associated_beer has gravity logging enabled)
        if self.has_gravity_enabled():
            if not self.can_log_gravity():
                # We have gravity enabled, but we can't actually log gravity. Stop logging, as this is an issue.
                self.associated_beer.device.manage_logging(status='stop')
                raise RuntimeError("Gravity enabled, but gravity sensor doesn't exist")

            self.gravity = self.associated_beer.device.gravity_sensor.retrieve_loggable_gravity()
            temp, temp_format = self.associated_beer.device.gravity_sensor.retrieve_loggable_temp()

            if self.temp_format != temp_format:
                if temp_format is None:
                    # No data exists in redis yet for this sensor
                    temp = None
                elif self.temp_format == 'C' and temp_format == 'F':
                    # Convert Fahrenheit to Celsius
                    temp = (temp-32) * 5 / 9
                elif self.temp_format == 'F' and temp_format == 'C':
                    # Convert Celsius to Fahrenheit
                    temp = (temp*9/5) + 32
                else:
                    logger.error("BeerLogPoint.enrich_gravity_data called with unsupported temp format {}".format(self.temp_format))

            self.gravity_temp = temp


    def data_point(self, data_format='base_csv', set_defaults=True):
        # Everything gets stored in UTC and then converted back on the fly

        utc_tz = pytz.timezone("UTC")
        time_value = self.log_time.astimezone(utc_tz).strftime('%Y/%m/%d %H:%M:%SZ')  # Adding 'Zulu' designation

        if set_defaults:
            beerTemp = self.beer_temp or 0
            fridgeTemp = self.fridge_temp or 0
            roomTemp = self.room_temp or 0
            beerSet = self.beer_set or 0
            fridgeSet = self.fridge_set or 0
            gravity_log = self.gravity or 0  # We'll set this just in case
            gravity_temp = self.gravity_temp or 0  # We'll set this just in case
        else:
            beerTemp = self.beer_temp or None
            fridgeTemp = self.fridge_temp or None
            roomTemp = self.room_temp or None
            beerSet = self.beer_set or None
            fridgeSet = self.fridge_set or None
            gravity_log = self.gravity or None  # We'll set this just in case
            gravity_temp = self.gravity_temp or None  # We'll set this just in case


        if self.beer_ann is not None:
            combined_annotation = self.beer_ann
        elif self.fridge_ann is not None:
            combined_annotation = self.fridge_ann
        else:
            combined_annotation = ""

        if data_format == 'base_csv':
            if not self.has_gravity_enabled():
                if self.associated_beer.model_version > 1:
                    return [time_value, beerTemp, beerSet, fridgeTemp, fridgeSet, roomTemp, self.state]
                else:
                    return [time_value, beerTemp, beerSet, fridgeTemp, fridgeSet, roomTemp]

            else:
                if self.associated_beer.model_version > 1:
                    return [time_value, beerTemp, beerSet, fridgeTemp, fridgeSet, roomTemp, gravity_log, gravity_temp,
                            self.state]
                else:
                    return [time_value, beerTemp, beerSet, fridgeTemp, fridgeSet, roomTemp, gravity_log, gravity_temp]

        elif data_format == 'full_csv':
            if not self.has_gravity_enabled():
                return [time_value, beerTemp, beerSet, self.beer_ann, fridgeTemp, fridgeSet, self.fridge_ann,
                        roomTemp, self.state, self.temp_format, self.associated_beer_id]
            else:
                return [time_value, beerTemp, beerSet, self.beer_ann, fridgeTemp, fridgeSet, self.fridge_ann,
                        roomTemp, self.state, self.temp_format, self.associated_beer_id, gravity_log, gravity_temp]

        elif data_format == 'annotation_json':
            retval = []
            if self.beer_ann is not None:
                retval.append({'series': 'beer_temp', 'x': time_value, 'shortText': self.beer_ann[:1],
                               'text': self.beer_ann})
            if self.fridge_ann is not None:
                retval.append({'series': 'beer_temp', 'x': time_value, 'shortText': self.fridge_ann[:1],
                               'text': self.fridge_ann})
            return retval
        else:
            # Should never hit this
            logger.warning("Invalid data format '{}' provided to BeerLogPoint.data_point".format(data_format))

    def save(self, *args, **kwargs):
        # Don't repeat yourself
        def check_and_write_headers(path, col_headers):
            if not os.path.exists(path):
                with open(path, 'w') as f:
                    writer = csv.writer(f)
                    writer.writerow(col_headers)

        def write_data(path, row_data):
            with open(path, 'a') as f:
                writer = csv.writer(f)
                writer.writerow(row_data)

        def check_and_write_annotation_json_head(path):
            if not os.path.exists(path):
                with open(path, 'w') as f:
                    f.write("[\r\n")
                return False
            else:
                return True

        def write_annotation_json(path, annotation_data, write_comma=True):
            # annotation_data is actually an array of potential annotations. We'll loop through them & write them out
            with open(path, 'a') as f:
                for this_annotation in annotation_data:
                    if write_comma:  # We only want to do this once per run, regardless of the size of annotation_data
                        f.write(',\r\n')
                        write_comma = False
                    f.write('  {')
                    f.write('"series": "{}", "x": "{}",'.format(this_annotation['series'], this_annotation['x']))
                    f.write(' "shortText": "{}", "text": "{}"'.format(this_annotation['shortText'],
                                                                      this_annotation['text']))
                    f.write('}')

        # This really isn't the right place to do this, but I don't know of anywhere else to add this check.
        # TODO - Figure out if there is somewhere better to do this
        if self.has_gravity_enabled() and self.associated_beer.device.gravity_sensor is None:
            # We're logging a gravity enabled beer, but there is no gravity sensor to pull data from. Stop logging.
            if self.associated_beer.device.active_beer == self.associated_beer:
                logger.error('Gravity sensor was deleted without cessation of logging on device {}. Logging has been force-stopped within BeerLogPoint.save()'.format(self.associated_beer.device_id))
                self.associated_beer.device.manage_logging(status='stop')
                return False

        if self.associated_beer_id is not None:
            file_name_base = os.path.join(settings.BASE_DIR, settings.DATA_ROOT, self.associated_beer.base_filename())

            base_csv_file = file_name_base + self.associated_beer.full_filename('base_csv', extension_only=True)
            full_csv_file = file_name_base + self.associated_beer.full_filename('full_csv', extension_only=True)
            annotation_json = file_name_base + self.associated_beer.full_filename('annotation_json', extension_only=True)

            # Write out headers (if the files don't exist)
            check_and_write_headers(base_csv_file, self.associated_beer.column_headers('base_csv'))
            check_and_write_headers(full_csv_file, self.associated_beer.column_headers('full_csv'))

            # And then write out the data
            write_data(base_csv_file, self.data_point('base_csv'))
            write_data(full_csv_file, self.data_point('full_csv'))

            # Next, do the json file
            annotation_data = self.data_point('annotation_json')
            if len(annotation_data) > 0:  # Not all log points come with annotation data
                json_existed = check_and_write_annotation_json_head(annotation_json)
                write_annotation_json(annotation_json, annotation_data, json_existed)

        # super(BeerLogPoint, self).save(*args, **kwargs)


# A model representing the fermentation profile as a whole
class FermentationProfile(models.Model):
    # Status Choices
    STATUS_ACTIVE = 1
    STATUS_PENDING_DELETE = 2

    STATUS_CHOICES = (
        (STATUS_ACTIVE, 'Active'),
        (STATUS_PENDING_DELETE, 'Pending Delete'),
    )

    # Profile Type Choices
    PROFILE_STANDARD = "Standard Profile"
    PROFILE_SMART = "Smart Profile"

    PROFILE_TYPE_CHOICES = (
        (PROFILE_STANDARD, 'Standard Profile'),
        (PROFILE_SMART, 'Smart Profile (Unimplemented)'),
    )

    # Export/Import Strings
    EXPORT_LEFT_WALL = "| "
    EXPORT_RIGHT_WALL = " |"
    EXPORT_COL_SEPARATOR = " | "
    EXPORT_COL_SEPARATOR_REGEX = r" \| "
    EXPORT_ROW_SEPARATOR = "="


    # Fields
    name = models.CharField(max_length=128)
    status = models.IntegerField(choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    
    profile_type = models.CharField(max_length=32, default=PROFILE_STANDARD, help_text="Type of temperature profile")


    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name



    # Test if this fermentation profile is currently being used by a beer
    def currently_in_use(self):
        try:
            num_devices_currently_using = BrewPiDevice.objects.filter(active_profile=self).count()
        except:
            num_devices_currently_using = 0

        if num_devices_currently_using > 0:
            return True
        else:
            return False

    # Due to the way we're implementing this, we don't want a user to be able to edit a profile that is currently in use
    def is_editable(self):
        return not self.currently_in_use()

    def is_pending_delete(self):
        return self.status == self.STATUS_PENDING_DELETE

    # An assignable profile needs to be active and have setpoints
    def is_assignable(self):
        if self.status != self.STATUS_ACTIVE:
            return False
        else:
            if self.fermentationprofilepoint_set is None:
                return False

        return True

    # If we attempt to delete a profile that is in use, we instead change the status. This runs through profiles in
    # this status and deletes those that are no longer in use.
    @classmethod
    def cleanup_pending_delete(cls):
        profiles_pending_delete = cls.objects.filter(status=cls.STATUS_PENDING_DELETE)
        for profile in profiles_pending_delete:
            if not profile.currently_in_use():
                profile.delete()


    # This function is designed to create a more "human readable" version of a temperature profile (to help people
    # better understand what a given profile is actually going to do).

    # I would prefer to implement this as part of a template (given that it's honestly display logic) but the Django
    # template language doesn't provide quite what I would need to pull it off.
    def to_english(self):
        profile_points = self.fermentationprofilepoint_set.order_by('ttl')

        description = []
        past_first_point=False  # There's guaranteed to be a better way to do this
        previous_setpoint = 0.0
        previous_ttl = 0.0

        if profile_points.__len__() < 1:
            description.append("This profile contains no setpoints and cannot be assigned.")

        # TODO - Make the timedelta objects more human readable (I don't like the 5:20:30 format that much)
        for this_point in profile_points:
            if not past_first_point:
                desc_text = "Start off by heating/cooling to {}&deg; {}".format(this_point.temp_to_preferred(), config.TEMPERATURE_FORMAT)

                if this_point.ttl == datetime.timedelta(seconds=0):
                    desc_text += "."
                else:
                    desc_text += " and hold this temperature for {}".format(this_point.ttl)

                description.append(desc_text)
                previous_setpoint = this_point.temp_to_preferred()
                previous_ttl = this_point.ttl
                past_first_point = True
            else:
                if previous_setpoint == this_point.temperature_setting:
                    desc_text = "Hold this temperature for {} ".format((this_point.ttl - previous_ttl))
                    desc_text += "(until {} after the profile was assigned).".format(this_point.ttl)
                else:
                    if previous_setpoint > this_point.temp_to_preferred():
                        desc_text = "Cool to"
                    else:  # If previous_setpoint is less than the current setpoint
                        desc_text = "Heat to"

                    # Breaking this up to reduce line length
                    desc_text += " {}&deg; {} ".format(this_point.temp_to_preferred(), config.TEMPERATURE_FORMAT)
                    desc_text += "over the next {} ".format(this_point.ttl - previous_ttl)
                    desc_text += "(reaching this temperature {}".format(this_point.ttl)
                    desc_text += " after the profile was assigned)."

                description.append(desc_text)
                previous_setpoint = this_point.temp_to_preferred()
                previous_ttl = this_point.ttl

        if past_first_point:
            desc_text = "Finally, permanently hold the temperature at {}&deg; {}.".format(previous_setpoint, config.TEMPERATURE_FORMAT)
            description.append(desc_text)

        return description

    # profile_temp replaces brewpi-script/temperatureProfile.py, and is intended to be called by
    # get_profile_temp from BrewPiDevice
    def profile_temp(self, time_started, temp_format):
        # temp_format in this case is the temperature format active on BrewPiDevice. This will force conversion from
        # the profile point's format to the device's format.
        profile_points = self.fermentationprofilepoint_set.order_by('ttl')

        past_first_point=False  # There's guaranteed to be a better way to do this
        previous_setpoint = 0.0
        previous_ttl = 0.0
        current_time = timezone.now()

        for this_point in profile_points:
            if not past_first_point:
                # If we haven't hit the first TTL yet, we are in the initial lag period where we hold a constant
                # temperature. Return the temperature setting
                if current_time < (time_started + this_point.ttl):
                    return this_point.convert_temp(temp_format)
                past_first_point = True
            else:
                # Test if we are in this period
                if current_time < (time_started + this_point.ttl):
                    # We are - Check if we need to interpolate, or if we can just use the static temperature
                    if this_point.convert_temp(temp_format) == previous_setpoint:  # We can just use the static temperature
                        return this_point.convert_temp(temp_format)
                    else:  # We have to interpolate
                        duration = this_point.ttl.total_seconds() - previous_ttl.total_seconds()
                        delta = (this_point.convert_temp(temp_format) - previous_setpoint)
                        slope = float(delta) / duration

                        seconds_into_point = (current_time - (time_started + previous_ttl)).total_seconds()

                        return round(seconds_into_point * slope + float(previous_setpoint), 1)

            previous_setpoint = this_point.convert_temp(temp_format)
            previous_ttl = this_point.ttl

        # If we hit this point, we looped through all the setpoints & aren't between two (or on the first one)
        # That is to say - we're at the end. Just return the last setpoint.
        return previous_setpoint

    # past_end_of_profile allows us to test if we're in the last stage of a profile (which is effectively beer constant
    # mode) so we can switch to explicitly be in beer constant mode
    def past_end_of_profile(self, time_started):
        current_time = timezone.now()

        last_profile_point = self.fermentationprofilepoint_set.order_by('-ttl')[:1]

        if last_profile_point:
            if current_time >= (time_started + last_profile_point[0].ttl):
                return True
            else:
                return False
        else:
            # There are no profile points for us to test against
            return None



    def to_export(self):
        # to_export generates a somewhat readable, machine interpretable representation of a fermentation profile

        def pad_to_width(string, width):
            if len(string) < width:
                for i in range(len(string), width):
                    string += " "
            return string

        def add_row_separator(width, no_walls=False):
            ret_string = ""
            if not no_walls:
                separator_width = width + len(self.EXPORT_LEFT_WALL) + len(self.EXPORT_RIGHT_WALL)
            else:
                separator_width = width
            for i in range(separator_width):
                ret_string += self.EXPORT_ROW_SEPARATOR
            return ret_string + "\r\n"

        profile_type = self.profile_type  # For future compatibility

        export_string = ""
        max_ttl_string = ""  # To enable me being lazy
        max_ttl_length = 0  # max_ttl_length is the maximum size of the left (ttl) column of the profile
        interior_width = 0  # Interior width is the interior size that can be occupied by data (wall to wall)

        point_set = self.fermentationprofilepoint_set.order_by('ttl')
        # We need to check there are any point_set yet
        if len(point_set) > 0:
            max_ttl_string = max([x.ttl_to_string(True) for x in point_set], key=len)
        max_ttl_length = len(max_ttl_string)

        # Set interior_width to the maximum interior width that we might need. This can be one of four things:
        # The length of the profile_type
        # The length of the profile.name
        # The maximum length of the two columns (max_ttl_length + self.EXPORT_COL_SEPARATOR + "-100.00 C"
        # The minimum table width (currently 30)
        interior_width = len(max([profile_type, self.name, (max_ttl_string + self.EXPORT_COL_SEPARATOR + "-100.00 C"),
                                  add_row_separator(30,no_walls=True)], key=len))

        # The header looks like this:
        # ===============================
        # | Profile Name                |
        # | Profile Type                |
        # ===============================

        export_string += add_row_separator(interior_width)
        export_string += self.EXPORT_LEFT_WALL + pad_to_width(self.name, interior_width) + self.EXPORT_RIGHT_WALL + "\r\n"
        export_string += self.EXPORT_LEFT_WALL + pad_to_width(profile_type, interior_width) + self.EXPORT_RIGHT_WALL + "\r\n"
        export_string += add_row_separator(interior_width)

        if profile_type == self.PROFILE_STANDARD:
            # For PROFILE_STANDARD profiles the body looks like this:
            # ===============================
            # | 3d4h  | 72.00 F             |
            # | 6d    | 64.00 F             |
            # ===============================
            for this_point in point_set:
                point_string = pad_to_width(this_point.ttl_to_string(short_code=True), max_ttl_length)
                point_string += self.EXPORT_COL_SEPARATOR + str(this_point.temperature_setting) + " " + this_point.temp_format
                export_string += self.EXPORT_LEFT_WALL + pad_to_width(point_string, interior_width) + self.EXPORT_RIGHT_WALL + "\r\n"

        export_string += add_row_separator(interior_width)

        return export_string

    @classmethod
    def import_from_text(cls, import_string):

        # Since we're going to loop through the entire profile in one go, track what parts of the profile we've captured
        found_initial_separator=False
        profile_name = u""
        profile_type = u""
        found_row_split = False
        profile_points = []
        found_profile_terminator = False

        for this_row in iter(import_string.splitlines()):
            if not found_initial_separator:
                if this_row.strip()[:10] == u"==========":
                    found_initial_separator = True
            elif profile_name == u"":
                profile_name = this_row.strip()[len(cls.EXPORT_LEFT_WALL):(len(this_row)-len(cls.EXPORT_RIGHT_WALL))].strip()
                if len(profile_name) > 128:
                    raise ValueError("Imported profile name is too long")
            elif profile_type == u"":
                profile_type = this_row.strip()[len(cls.EXPORT_LEFT_WALL):(len(this_row)-len(cls.EXPORT_RIGHT_WALL))].strip()

                if profile_type not in [x for x, _ in cls.PROFILE_TYPE_CHOICES]:
                    raise ValueError("Invalid profile type specified, or missing initial row separator")
            elif not found_row_split:
                if this_row.strip()[:10] == u"==========":
                    found_row_split = True
                else:
                    raise ValueError("Unable to locate divider between header & profile point list")
            elif not found_profile_terminator:
                if this_row.strip()[:10] == u"==========":
                    # We've found the profile terminator - tag found_profile_terminator and break
                    found_profile_terminator = True
                    break
                else:
                    # Before we do anything else, strip out the actual data (remove left/right wall & whitespace)
                    profile_data = this_row.strip()[len(cls.EXPORT_LEFT_WALL):(len(this_row)-len(cls.EXPORT_RIGHT_WALL))].strip()

                    try:
                        if profile_type == cls.PROFILE_STANDARD:
                            # For PROFILE_STANDARD profiles the body looks like this:
                            # ===============================
                            # | 3d 4h | 72.00 F             |
                            # | 6d    | 64.00 F             |
                            # ===============================
                            point_pattern = r"(?P<time_str>[0-9ywdhms]+)[ ]*" + cls.EXPORT_COL_SEPARATOR_REGEX + \
                                                    r"(?P<temp_str>[0-9\.]+) (?P<temp_fmt>[CF]{1})"
                        else:
                            raise ValueError("Unsupported profile type specified")

                        point_regex = re.compile(point_pattern)
                        point_matches = point_regex.finditer(this_row)
                    except:
                        raise ValueError("{} isn't in a valid format for conversion".format(profile_data))

                    for this_match in point_matches:
                        if profile_type == cls.PROFILE_STANDARD:
                            try:
                                ttl = FermentationProfilePoint.string_to_ttl(this_match.group('time_str'))
                            except ValueError:
                                raise ValueError("Invalid time string for row {}".format(profile_data))
                            profile_points.append({'ttl': ttl,
                                                   'temperature_setting': float(this_match.group('temp_str')),
                                                   'temp_format': this_match.group('temp_fmt')})
                        else:
                            raise ValueError("Unsupported profile type specified")

        if found_profile_terminator:
            # At this point, we've imported the full profile. If there are no profile points, raise an error. Otherwise,
            # attempt to create the various objects

            if len(profile_points) <= 0:
                raise ValueError("No points in provided profile")

            if profile_type == cls.PROFILE_STANDARD:
                new_profile = cls(name=profile_name, profile_type=profile_type)
                new_profile.save()

                for this_point in profile_points:
                    new_point = FermentationProfilePoint(profile=new_profile, ttl=this_point['ttl'],
                                                         temperature_setting=this_point['temperature_setting'],
                                                         temp_format=this_point['temp_format'])
                    new_point.save()

                # And we're done. Return the new_profile object
                return new_profile

            else:
                raise ValueError("Unsupported profile type specified")
        else:
            raise ValueError("No profile terminator found")

    def copy_to_new(self, name):
        # This copies the current fermentation profile to a new profile

        if len(name) <= 0:
            raise ValueError("Name provided is too short")

        new_profile = FermentationProfile(name=name, profile_type=self.profile_type)
        new_profile.save()

        for this_point in self.fermentationprofilepoint_set.all():
            new_point = FermentationProfilePoint(profile=new_profile, temp_format=this_point.temp_format,
                                                 ttl=this_point.ttl, temperature_setting=this_point.temperature_setting)
            new_point.save()

        return new_profile


class FermentationProfilePoint(models.Model):
    TEMP_FORMAT_CHOICES = (('C', 'Celsius'), ('F', 'Fahrenheit'))

    profile = models.ForeignKey(FermentationProfile, on_delete=models.CASCADE)
    ttl = models.DurationField(help_text="Time at which we should arrive at this temperature")
    temperature_setting = models.DecimalField(max_digits=5, decimal_places=2, null=True,
                                              help_text="The temperature the beer should be when TTL has passed")
    temp_format = models.CharField(max_length=1, default='F')

    def temp_to_f(self):
        if self.temp_format == 'F':
            return self.temperature_setting
        else:
            return (self.temperature_setting*9/5) + 32

    def temp_to_c(self):
        if self.temp_format == 'C':
            return self.temperature_setting
        else:
            return (self.temperature_setting-32) * 5 / 9

    def temp_to_preferred(self):
        # Converts the point to whatever the preferred temperature format is per Constance
        if config.TEMPERATURE_FORMAT == 'F':
            return self.temp_to_f()
        elif config.TEMPERATURE_FORMAT == 'C':
            return self.temp_to_c()
        pass

    def convert_temp(self, desired_temp_format):
        if self.temp_format == desired_temp_format:
            return self.temperature_setting
        elif self.temp_format == 'F' and desired_temp_format == 'C':
            return self.temp_to_c()
        elif self.temp_format == 'C' and desired_temp_format == 'F':
            return self.temp_to_f()
        else:
            logger.error("Invalid temperature format {} specified".format(desired_temp_format))
            return self.temperature_setting

    def ttl_to_string(self, short_code=False):
        # This function returns self.ttl in the "5d 3h 4m 15s" format we use to key it in
        ttl_string = ""

        remainder = self.ttl.total_seconds()
        days, remainder = divmod(remainder, 60*60*24)
        hours, remainder = divmod(remainder, 60*60)
        minutes, seconds = divmod(remainder, 60)

        if short_code:
            day_string = "d"
            hour_string = "h"
            minute_string = "m"
            second_string = "s"
        else:
            day_string = " days, "
            hour_string = " hours, "
            minute_string = " minutes, "
            second_string = " seconds, "

        if days > 0:
            ttl_string += str(int(days)) + day_string
        if hours > 0:
            ttl_string += str(int(hours)) + hour_string
        if minutes > 0:
            ttl_string += str(int(minutes)) + minute_string
        if seconds > 0:
            ttl_string += str(int(seconds)) + second_string

        if len(ttl_string) <=0:  # Default to 0 seconds
            ttl_string = "0" + second_string

        return ttl_string.rstrip(", ")

    @staticmethod
    def string_to_ttl(string):
        if len(string) <= 1:
            raise ValueError("No string provided to convert")

        # Split out the d/h/m/s of the timer
        try:
            timer_pattern = r"(?P<time_amt>[0-9]+)[ ]*(?P<ywdhms>[ywdhms]{1})"
            timer_regex = re.compile(timer_pattern)
            timer_matches = timer_regex.finditer(string)
        except:
            raise ValueError("{} isn't in a valid format for conversion".format(string))


        # timer_time is equal to now + the time delta
        time_delta = datetime.timedelta(seconds=0)
        for this_match in timer_matches:
            dhms = this_match.group('ywdhms')
            delta_amt = int(this_match.group('time_amt'))
            if dhms == 'y':  # This doesn't account for leap years, but whatever.
                time_delta = time_delta + datetime.timedelta(days=(365*delta_amt))
            elif dhms == 'w':
                time_delta = time_delta + datetime.timedelta(weeks=delta_amt)
            elif dhms == 'd':
                time_delta = time_delta + datetime.timedelta(days=delta_amt)
            elif dhms == 'h':
                time_delta = time_delta + datetime.timedelta(hours=delta_amt)
            elif dhms == 'm':
                time_delta = time_delta + datetime.timedelta(minutes=delta_amt)
            elif dhms == 's':
                time_delta = time_delta + datetime.timedelta(seconds=delta_amt)

        return time_delta



# The old (0.2.x/Arduino) Control Constants Model
class OldControlConstants(models.Model):

    tempSetMin = models.FloatField(
        verbose_name="Min Temperature",
        help_text="The fridge and beer temperatures cannot go below this value. Units are specified by 'Temperature " +
                  "format' below.",
        )
    tempSetMax = models.FloatField(
        verbose_name="Max Temperature",
        help_text="The fridge and beer temperatures cannot go above this value. Units are specified by 'Temperature " +
                  "format' below.",
        )
    Kp = models.FloatField(
        verbose_name="PID: Kp",
        help_text="The beer temperature error is multiplied by Kp to give the proportional of the PID value"
        )
    Ki = models.FloatField(
        verbose_name="PID: Ki",
        help_text="When the integral is active, the error is added to the integral every 30 sec. The result is " +
                  "multiplied by Ki to give the integral part."
        )
    Kd = models.FloatField(
        verbose_name="PID: Kd",
        help_text="The derivative of the beer temperature is multiplied by " +
                  "Kd to give the derivative part of the PID value"
        )
    pidMax = models.FloatField(
        verbose_name="PID: maximum",
        help_text="Defines the maximum difference between the beer temp setting and fridge temp setting. The fridge " +
                  "setting will be clipped to this range."
        )
    iMaxErr = models.FloatField(
        verbose_name="Integrator: Max temp error C",
        help_text="The integral is only active when the temperature is close to the target temperature. This is the " +
                  "maximum error for which the integral is active."
    )
    idleRangeH = models.FloatField(
        verbose_name="Temperature idle range top",
        help_text="When the fridge temperature is within this range, it " +
                  "will not heat or cool, regardless of other settings"
    )
    idleRangeL = models.FloatField(
        verbose_name="Temperature idle range bottom",
        help_text="When the fridge temperature is within this range, it " +
                  "will not heat or cool, regardless of other settings"
    )
    heatTargetH = models.FloatField(
        verbose_name="Heating target upper bound",
        help_text="When the overshoot lands under this value, the peak " +
                  "is within the target range and the estimator is not adjusted"
    )
    heatTargetL = models.FloatField(
        verbose_name="Heating target lower bound",
        help_text="When the overshoot lands above this value, the peak " +
                  "is within the target range and the estimator is not adjusted"
    )
    coolTargetH = models.FloatField(
        verbose_name="Cooling target upper bound",
        help_text="When the overshoot lands under this value, the peak " +
                  "is within the target range and the estimator is not adjusted"
    )
    coolTargetL = models.FloatField(
        verbose_name="Cooling target lower bound",
        help_text="When the overshoot lands above this value, the peak " +
                  "is within the target range and the estimator is not adjusted"
    )

    maxHeatTimeForEst = models.IntegerField(
        verbose_name="Maximum time in seconds for heating overshoot estimator",
        help_text="The time the fridge has been heating is used to estimate overshoot. " +
                  "This is the maximum time that is taken into account."
    )
    maxCoolTimeForEst = models.IntegerField(
        verbose_name="Maximum time in seconds for cooling overshoot estimator",
        help_text="Maximum time the fridge has been cooling is used to estimate " +
                  "overshoot. This is the maximum time that is taken into account."
    )
    beerFastFilt = models.IntegerField(
        verbose_name="Beer fast filter delay time",
        help_text="The beer fast filter is used for display and data logging. " +
                  "More filtering gives a smoother line but also more delay."
    )
    beerSlowFilt = models.IntegerField(
        verbose_name="Beer slow filter delay time",
        help_text="The beer slow filter is used for the control algorithm. " +
                  "The fridge temperature setting is calculated from this filter. " +
                  "Because a small difference in beer temperature cases a large " +
                  "adjustment in the fridge temperature, more smoothing is needed."
    )
    beerSlopeFilt = models.IntegerField(
        verbose_name="Beer slope filter delay time",
        help_text="The slope is calculated every 30 sec and fed to this filter. " +
                  "More filtering means a smoother fridge setting."
    )
    fridgeFastFilt = models.IntegerField(
        verbose_name="Fridge fast filter delay time",
        help_text="The fridge fast filter is used for on-off control, display, " +
                  "and logging. It needs to have a small delay."
    )
    fridgeSlowFilt = models.IntegerField(
        verbose_name="Fridge slow filter delay time",
        help_text="The fridge slow filter is used for peak detection to adjust " +
                  "the overshoot estimators. More smoothing is needed to prevent " +
                  "small fluctuations from being recognized as peaks."
    )
    fridgeSlopeFilt = models.IntegerField(
        verbose_name="Fridge slope filter delay time",
        help_text="Fridge slope filter is not used in this revision of the firmware."
    )

    lah = models.IntegerField(
        verbose_name="Using light as heater?",
        help_text="If set to yes the chamber light (if assigned a pin) will be used in place of the heat pin",
        choices=(
            (1, "YES"),
            (0, "No")
        ),
        default=0
    )

    hs = models.IntegerField(
        verbose_name="Use half steps for rotary encoder?",
        help_text="If this option is set to yes, the rotary encoder will use half steps",
        choices=(
            (1, "YES"),
            (0, "No")
        ),
        default=0
    )

    tempFormat = models.CharField(
        verbose_name="Temperature format",
        help_text="This is the temperature format that will be used by the device",
        max_length=1,
        choices=(
            ("F", "Fahrenheit"),
            ("C", "Celsius")
        ),
        default='F'
        )

    # In a lot of cases we're selectively loading/sending/comparing the fields that are known by the firmware
    # To make it easy to iterate over those fields, going to list them out here
    firmware_field_list = ['tempSetMin', 'tempSetMax', 'Kp', 'Ki', 'Kd', 'pidMax', 'iMaxErr', 'idleRangeH',
                           'idleRangeL', 'heatTargetH', 'heatTargetL', 'coolTargetH', 'coolTargetL',
                           'maxHeatTimeForEst', 'maxCoolTimeForEst', 'beerFastFilt', 'beerSlowFilt', 'beerSlopeFilt',
                           'fridgeFastFilt', 'fridgeSlowFilt', 'fridgeSlopeFilt', 'lah', 'hs', 'tempFormat']

    # preset_name is only used if we want to save the preset to the database to be reapplied later
    preset_name = models.CharField(max_length=255, null=True, blank=True, default="")

    def load_from_controller(self, controller):
        """
        :param controller: models.BrewPiDevice
        :type controller: BrewPiDevice
        :return: boolean
        """
        # try:
        # Load the control constants dict from the controller
        cc = controller.get_control_constants()

        for this_field in self.firmware_field_list:
            try:
                # In case we don't get every field back
                setattr(self, this_field, cc[this_field])
            except:
                pass
        return True

        # except:
        #     return False

    def save_to_controller(self, controller, attribute):
        """
        :param controller: models.BrewPiDevice
        :type controller: BrewPiDevice
        :return:
        """

        value_to_send = {attribute: getattr(self, attribute)}
        return controller.set_parameters(value_to_send)

    def save_all_to_controller(self, controller, prior_control_constants=None):
        """
        :param controller: models.BrewPiDevice
        :type controller: BrewPiDevice
        :return: boolean
        """

        if prior_control_constants is None:
            # Load the preexisting control constants from the controller
            prior_control_constants = OldControlConstants()
            prior_control_constants.load_from_controller(controller)

        for this_field in self.firmware_field_list:
            # Now loop through and check each field to find out what changed
            if getattr(self, this_field) != getattr(prior_control_constants, this_field):
                # ...and only update those fields
                self.save_to_controller(controller, this_field)
        return True




# The new (0.4.x/Spark) Control Constants Model
class NewControlConstants(models.Model):
    # class Meta:
    #     managed = False

    tempFormat = models.CharField(max_length=1,default="C")

    # settings for heater 1
    heater1_kp = models.FloatField(help_text="Actuator output in % = Kp * input error")
    heater1_ti = models.IntegerField()
    heater1_td = models.IntegerField()
    heater1_infilt = models.IntegerField()
    heater1_dfilt = models.IntegerField()

    # settings for heater 2
    heater2_kp = models.FloatField()
    heater2_ti = models.IntegerField()
    heater2_td = models.IntegerField()
    heater2_infilt = models.IntegerField()
    heater2_dfilt = models.IntegerField()

    # settings for cooler
    cooler_kp = models.FloatField()
    cooler_ti = models.IntegerField()
    cooler_td = models.IntegerField()
    cooler_infilt = models.IntegerField()
    cooler_dfilt = models.IntegerField()

    # settings for beer2fridge PID
    beer2fridge_kp = models.FloatField()
    beer2fridge_ti = models.IntegerField()
    beer2fridge_td = models.IntegerField()
    beer2fridge_infilt = models.IntegerField()
    beer2fridge_dfilt = models.IntegerField()
    beer2fridge_pidMax = models.FloatField()

    minCoolTime = models.IntegerField()
    minCoolIdleTime = models.IntegerField()
    heater1PwmPeriod = models.IntegerField()
    heater2PwmPeriod = models.IntegerField()
    coolerPwmPeriod = models.IntegerField()
    mutexDeadTime = models.IntegerField()

    # preset_name is only used if we want to save the preset to the database to be reapplied later
    preset_name = models.CharField(max_length=255, null=True, blank=True, default="")

    # In a lot of cases we're selectively loading/sending/comparing the fields that are known by the firmware
    # To make it easy to iterate over those fields, going to list them out here
    firmware_field_list = ['tempFormat', 'heater1_kp', 'heater1_ti', 'heater1_td', 'heater1_infilt', 'heater1_dfilt',
                           'heater2_kp', 'heater2_ti', 'heater2_td', 'heater2_infilt', 'heater2_dfilt',
                           'cooler_kp', 'cooler_ti', 'cooler_td', 'cooler_infilt', 'cooler_dfilt',
                           'beer2fridge_kp', 'beer2fridge_ti', 'beer2fridge_td', 'beer2fridge_infilt',
                           'beer2fridge_dfilt', 'beer2fridge_pidMax', 'minCoolTime', 'minCoolIdleTime',
                           'heater1PwmPeriod', 'heater2PwmPeriod', 'coolerPwmPeriod', 'mutexDeadTime',]


    def load_from_controller(self, controller):
        """
        :param controller: models.BrewPiDevice
        :type controller: BrewPiDevice
        :return: boolean
        """
        try:
            # Load the control constants dict from the controller
            cc = controller.get_control_constants()

            for this_field in self.firmware_field_list:
                setattr(self, this_field, cc[this_field])
            return True

        except:
            return False

    def save_to_controller(self, controller, attribute):
        """
        :param controller: models.BrewPiDevice
        :type controller: BrewPiDevice
        :return:
        """

        value_to_send = {attribute: getattr(self, attribute)}
        return controller.set_parameters(value_to_send)

    def save_all_to_controller(self, controller, prior_control_constants=None):
        """
        :param controller: models.BrewPiDevice
        :type controller: BrewPiDevice
        :return: boolean
        """
        try:
            for this_field in self.firmware_field_list:
                self.save_to_controller(controller, this_field)
            return True
        except:
            return False

# TODO - Determine if we care about controlSettings
# # There may only be a single control settings object between both revisions of the firmware, but I'll break it out
# # for now just in case.
# class OldControlSettings(models.Model):
#     class Meta:
#         managed = False
#
#     firmware_field_list = ['tempSetMin', 'tempSetMax', 'Kp', 'Ki', 'Kd', 'pidMax', 'iMaxErr', 'idleRangeH',
#                            'idleRangeL', 'heatTargetH', 'heatTargetL', 'coolTargetH', 'coolTargetL',
#                            'maxHeatTimeForEst', 'maxCoolTimeForEst', 'beerFastFilt', 'beerSlowFilt', 'beerSlopeFilt',
#                            'fridgeFastFilt', 'fridgeSlowFilt', 'fridgeSlopeFilt', 'lah', 'hs',]
#
#     controller = models.ForeignKey(BrewPiDevice)
#
#     def load_from_controller(self, controller=None):
#         """
#         :param controller: models.BrewPiDevice
#         :type controller: BrewPiDevice
#         :return: boolean
#         """
#         if controller is not None:
#             self.controller = controller
#         try:
#             cc = json.loads(self.controller.send_message("getControlSettings", read_response=True))
#
#             for this_field in self.firmware_field_list:
#                 setattr(self, this_field, cc[this_field])
#             return True
#
#         except:
#             return False
#
#     def save_to_controller(self, controller, attribute):
#         """
#         :param controller: models.BrewPiDevice
#         :type controller: BrewPiDevice
#         :return:
#         """
#
#         value_to_send = {attribute, getattr(self, attribute)}
#         return controller.send_message("setParameters", json.dumps(value_to_send))
#
#     def save_all_to_controller(self, controller, prior_control_constants=None):
#         """
#         :param controller: models.BrewPiDevice
#         :type controller: BrewPiDevice
#         :return: boolean
#         """
#         try:
#             for this_field in self.firmware_field_list:
#                 self.save_to_controller(controller, this_field)
#             return True
#         except:
#             return False
#
