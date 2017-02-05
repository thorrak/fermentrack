from __future__ import unicode_literals

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

import socket
import json, time, datetime, pytz
from constance import config
from brewpi_django import settings


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
        new_device = cls(text=device_dict['text'], type=device_dict['type'], pin=device_dict['val'])
        return new_device

    # load_all_from_pinlist returns a list of available pin objects
    @classmethod
    def load_all_from_pinlist(cls, pinlist):
        all_pins = []

        for this_pin in pinlist:
            next_pin = cls.create_from_dict(this_pin)
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


    # TODO - Rename these to make them more user friendly
    DEVICE_FUNCTION_CHOICES = (
        (DEVICE_FUNCTION_NONE,          'NONE'),
        (DEVICE_FUNCTION_CHAMBER_DOOR,  'CHAMBER_DOOR'),
        (DEVICE_FUNCTION_CHAMBER_HEAT,  'CHAMBER_HEAT'),
        (DEVICE_FUNCTION_CHAMBER_COOL,  'CHAMBER_COOL'),
        (DEVICE_FUNCTION_CHAMBER_LIGHT, 'CHAMBER_LIGHT'),
        (DEVICE_FUNCTION_CHAMBER_TEMP,  'CHAMBER_TEMP'),
        (DEVICE_FUNCTION_CHAMBER_ROOM_TEMP, 'CHAMBER_ROOM_TEMP'),
        (DEVICE_FUNCTION_CHAMBER_FAN,   'CHAMBER_FAN'),
        (DEVICE_FUNCTION_MANUAL_ACTUATOR, 'CHAMBER_RESERVED1'),   # Unused, reserved for future use - Tagged as "Manual Actuator" in develop www
        (DEVICE_FUNCTION_BEER_TEMP,     'BEER_TEMP'),           # Primary beer temp sensor
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

        #  TODO - Determine if I should error out if we don't receive 'h' back in the dict, or should allow defaulting
        if 'h' in device_dict:  # const char DEVICE_ATTRIB_HARDWARE = 'h';
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
            new_device.invert = device_dict['x']

        if pinlist_dict:
            for this_pin in pinlist_dict:
                if this_pin.pin == new_device.pin:
                    new_device.pin_data = this_pin

        return new_device


    @classmethod
    def load_all_from_devicelist(cls, device_list, pinlist_dict=None, controller=None):
        all_devices = []

        for this_device in device_list:
            next_device = cls.create_from_dict(this_device, pinlist_dict)
            next_device.controller = controller
            all_devices.append(next_device)

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

        # ARGH - TODO - Remember how to combine the next two lines of code
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
    def write_config_to_controller(self):
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

        return self.controller.send_message("applyDevice", json.dumps(config_dict))

    # Uninstall basically just sets device_function to 0
    def uninstall(self):
        self.device_function = SensorDevice.DEVICE_FUNCTION_NONE
        # Technically, the next 2 are overwritten in write_config_to_controller, but explicitly breaking them out here
        self.chamber = 0
        self.beer = 0

        return self.write_config_to_controller()

    @staticmethod
    def find_device_from_address_or_pin(device_list, address=None, pin=None):
        if address is not None and len(address) > 0:
            for this_device in device_list:
                if this_device.address == address:
                    return this_device
        elif pin is not None:
            for this_device in device_list:
                if this_device.pin == pin:
                    return this_device

        return None  # Either we weren't passed address or pin, or we weren't able to locate a valid device



#{"beerName": "Sample Data", "tempFormat": "C", "profileName": "Sample Profile", "dateTimeFormat": "yy-mm-dd", "dateTimeFormatDisplay": "mm/dd/yy" }
class BrewPiDevice(models.Model):
    """
    BrewPiDevice is the rough equivalent to an individual installation of brewpi-www
    """

    class Meta:
        verbose_name = "BrewPi Device"
        verbose_name_plural = "BrewPi Devices"


    TEMP_FORMAT_CHOICES = (('C', 'Celsius'), ('F', 'Fahrenheit'))
    DATA_LOGGING_CHOICES = (('active', 'Active'), ('paused', 'Paused'), ('stopped', 'Stopped'))
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
    CONNECTION_TYPE_CHOICES = (
        ('serial', 'Serial (Arduino and others)'),
        ('wifi', 'WiFi (ESP8266)'),
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

#    active_beer = models.ForeignKey()

    device_name = models.CharField(max_length=48, help_text="Unique name for this device", unique=True)

    # This is set at the device level, and should probably be read from the device as well. Going to include here
    # to cache it.
    temp_format = models.CharField(max_length=1, choices=TEMP_FORMAT_CHOICES, default='C', help_text="Temperature units")

    data_point_log_interval = models.IntegerField(default=10, choices=DATA_POINT_TIME_CHOICES,
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
    logging_status = models.CharField(max_length=10, choices=DATA_LOGGING_CHOICES, default='stopped', help_text="Data logging status")

    serial_port = models.CharField(max_length=255, help_text="Serial port to which the BrewPi device is connected",
                                   default="auto")
    serial_alt_port = models.CharField(max_length=255, help_text="Alternate serial port to which the BrewPi device is connected (??)",
                                   default="None")
    board_type = models.CharField(max_length=10, default="uno", choices=BOARD_TYPE_CHOICES, help_text="Board type to which BrewPi is connected")

    # TODO - Add some kind of helper function to test if process_id is valid, and reset to 0 if it is not.
    process_id = models.IntegerField(default=0)

    # Replaces the 'do not run' file used by brewpi-script
    status = models.CharField(max_length=15, default=STATUS_ACTIVE, choices=STATUS_CHOICES)

    socket_name = models.CharField(max_length=25, default="BEERSOCKET",
                                   help_text="Name of the file-based socket (Only used if useInetSocket is False)")

    connection_type = models.CharField(max_length=15, default='serial', choices=CONNECTION_TYPE_CHOICES,
                                       help_text="Type of connection between the Raspberry Pi and the hardware")
    wifi_host = models.CharField(max_length=40, default='None',
                                 help_text="mDNS host name or IP address for WiFi connected hardware (only used if " +
                                           "connection_type is wifi)")
    wifi_port = models.IntegerField(default=23, validators=[MinValueValidator(10,"Port must be 10 or higher"),
                                                            MaxValueValidator(65535, "Port must be 65535 or lower")],
                                    help_text="The internet socket to use (only used if connection_type is wifi)")

    # The beer that is currently active & being logged
    active_beer = models.ForeignKey('Beer', null=True, blank=True, default=None)

    # The active fermentation profile (if any!)
    active_profile = models.ForeignKey('FermentationProfile', null=True, blank=True, default=None)

    # The time the fermentation profile was applied (all our math is based on this)
    time_profile_started = models.DateTimeField(null=True, blank=True, default=None)

    def get_profile_temp(self):
        # If the object is inconsistent, don't return anything
        if self.active_profile is None:
            return None
        if self.time_profile_started is None:
            return None

        return self.active_profile.profile_temp(self.time_profile_started)

    # Other things that aren't persisted in the database
    # available_devices = []
    # installed_devices = []
    # devices_are_loaded = False

    def __str__(self):
        return self.device_name

    def send_message_to_device(self, message_type, message_contents=""):
        pass

    def read_lcd_from_device(self):
        pass

    def get_active_beer_name(self):
        if self.active_beer:
            return self.active_beer.name
        else:
            return ""


    # def get_active_beer_id(self, chamber_no=1):
    #     # TODO - Finish this (or don't, if I no longer need it)
    #     try:
    #         active_beer = self.chamber_set.get(chamber_no=chamber_no).active_beer
    #         return active_beer.id
    #     except:
    #         pass
    #
    # def set_active_beer_id(self, beer_id, chamber_no=1):
    #     active_chamber, created = self.chamber_set.get_or_create(brewpi_device=self.id, chamber_no = chamber_no)
    #     active_chamber.active_beer_id = beer_id
    #     active_chamber.save()


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
                # TODO - Determine if I need to change the timeouts
                # this_socket.setsockopt()
            except:
                # TODO - Something here. We failed to connect to the socket.
                this_socket.close()

        return this_socket

    def write_to_socket(self, this_socket, message):
        try:
            this_socket.sendall(message)
            return True
        except:
            # TODO - Do something here
            return False

    def read_from_socket(self, this_socket):
        try:
            return this_socket.recv(65536)
        except:
            return None

    # TODO - Rename this
    def send_and_receive_from_socket(self, message):
        this_socket = self.open_socket()
        if this_socket:
            if self.write_to_socket(this_socket, message):
                return self.read_from_socket(this_socket)
        return None


    def read_lcd(self):
        try:
            lcd_text = json.loads(self.send_and_receive_from_socket("lcd"))
        except:
            lcd_text = ["Cannot receive", "LCD text from", "Controller/Script"]
        return lcd_text

    def send_message(self, message, message_extended=None):
        message_to_send = message
        if message_extended is not None:
            message_to_send += "=" + message_extended
        this_socket = self.open_socket()
        if this_socket:
            if self.write_to_socket(this_socket, message_to_send):
                return True
        return False

    def retrieve_version(self):
        try:
            version_data = json.loads(self.send_and_receive_from_socket("getVersion"))
        except:
            return None
        return version_data

    def is_legacy(self, version=None):
        if version == None:
            version = self.retrieve_version()
            if not version:
                # If we weren't passed a version & can't load from the device itself, return None
                return None  # There's probably a better way of doing this.

        if version['version'] == "0.2.4":
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

    # We don't persist the "sensor" (onewire/pin) list in the database, so we always have to load it from the
    # controller
    def load_sensors_from_device(self):
        try:
            if self.devices_are_loaded:
                return True
        except:
            self.devices_are_loaded = False

        # Note - getDeviceList actually is reading the cache from brewpi-script - not the firmware itself
        loop_number = 0
        device_response = self.send_and_receive_from_socket("getDeviceList")
        while device_response == "device-list-not-up-to-date" and loop_number < 6:
            self.send_message("refreshDeviceList")  # refreshDeviceList refreshes the cache within brewpi-script
            time.sleep(4)  # This is a horrible practice, and I feel dirty just writing it.
            device_response = self.send_and_receive_from_socket("getDeviceList")
            loop_number += 1

        if not device_response:
            # We weren't able to reach brewpi-script
            self.all_pins = None
            self.available_devices = None
            self.installed_devices = None
            self.devices_are_loaded = False
            self.error_message = "Unable to reach brewpi-script. Try restarting brewpi-script."
            return self.devices_are_loaded  # False
        elif device_response == "device-list-not-up-to-date":
            # We were able to reach brewpi-script, but it wasn't able to reach the controller
            self.all_pins = None
            self.available_devices = None
            self.installed_devices = None
            self.devices_are_loaded = False
            self.error_message = "BrewPi-script wasn't able to load sensors from the controller. "
            self.error_message += "Try restarting brewpi-script. If that fails, try restarting the controller."
            return self.devices_are_loaded  # False

        devices = json.loads(device_response)
        self.all_pins = PinDevice.load_all_from_pinlist(devices['pinList'])
        self.available_devices = SensorDevice.load_all_from_devicelist(devices['deviceList']['available'], self.all_pins, self)
        self.installed_devices = SensorDevice.load_all_from_devicelist(devices['deviceList']['installed'], self.all_pins, self)
        self.devices_are_loaded = True

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

        return self.devices_are_loaded  # True

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

    def sync_temp_format(self):
        # This queries the controller to see if we have the correct tempFormat set (If it matches what is specified
        # in the device definition above). If it doesn't, we overwrite what is on the device to match what is in the
        # device definition.
        control_constants, legacy_mode = self.retrieve_control_constants()

        if control_constants.tempFormat != self.temp_format:  # The device has the wrong tempFormat - We need to update
            control_constants.tempFormat = self.temp_format

            if legacy_mode:
                if self.temp_format == 'C':
                    control_constants.tempSetMax = 30.0
                    control_constants.tempSetMin = 1.0
                elif self.temp_format == 'F':
                    control_constants.tempSetMax = 86.0
                    control_constants.tempSetMin = 33.0
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
        device_mode = self.send_and_receive_from_socket("getMode")

        if device_mode is not None:  # If we could connect to the device, force-sync the temp format
            self.sync_temp_format()

        control_status = {}
        if device_mode is None:  # We were unable to read from the device
            control_status['device_mode'] = "unable_to_connect"  # Not sure if I want to pass the message back this way

        elif device_mode == 'o':  # Device mode is off
            control_status['device_mode'] = "off"
            pass

        elif device_mode == 'b':  # Device mode is beer constant
            control_status['device_mode'] = "beer_constant"
            control_status['set_temp'] = self.send_and_receive_from_socket("getBeer")

        elif device_mode == 'f':  # Device mode is fridge constant
            control_status['device_mode'] = "fridge_constant"
            control_status['set_temp'] = self.send_and_receive_from_socket("getFridge")

        elif device_mode == 'p':  # Device mode is beer profile
            control_status['device_mode'] = "beer_profile"
            pass

        else:
            # No idea what the device mode is
            # TODO - Log this
            pass

        return control_status

    def reset_profile(self):
        if self.active_profile is not None:
            self.active_profile = None
        if self.time_profile_started is not None:
            self.time_profile_started = None
        self.save()

    def set_temp_control(self, method, set_temp=None, profile=None):
        if method == "off":
            self.reset_profile()
            self.send_message("setOff")
        elif method == "beer_constant":
            if set_temp is not None:
                self.reset_profile()
                self.send_message("setBeer", str(set_temp))
            else:
                return False
        elif method == "fridge_constant":
            if set_temp is not None:
                self.reset_profile()
                self.send_message("setFridge", str(set_temp))
            else:
                return False
        elif method == "beer_profile":
            try:
                ferm_profile = FermentationProfile.objects.get(id=profile)
            except:
                return False

            if not ferm_profile.is_assignable():
                return False

            self.active_profile = ferm_profile

            timezone_obj = pytz.timezone(getattr(settings, 'TIME_ZONE', 'UTC'))
            self.time_profile_started = datetime.datetime.now(tz=timezone_obj)

            self.save()

            self.send_message("setActiveProfile", str(self.active_profile.id))

        return True  # If we made it here, return True (we did our job)


class Beer(models.Model):
    # Beers are unique based on the combination of their name & the original device
    name = models.CharField(max_length=255, db_index=True)
    device = models.ForeignKey(BrewPiDevice, db_index=True)
    created = models.DateTimeField(default=timezone.now)


    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.__str__()

class BeerLogPoint(models.Model):
    """
    BeerLogPoint contains the individual temperature log points we're saving
    """

    class Meta:
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

    associated_beer = models.ForeignKey(Beer, db_index=True)

    @staticmethod
    def column_headers():
        return ['log_time', 'beer_temp', 'fridge_temp']

    def data_point(self):
        # datetime.datetime(1970, 1, 1)).total_seconds()
        # 1333238400.0
        # self.log_time.strftime('%Y/%m/%d %H:%M:%S')
        # time_value = int(time.mktime(self.log_time.timetuple()) * 1000)
        time_value = self.log_time.strftime('%Y/%m/%d %H:%M:%S')
        if self.beer_temp:
            beerTemp = self.beer_temp
        else:
            beerTemp = 0

        if self.fridge_temp:
            fridgeTemp = self.fridge_temp
        else:
            fridgeTemp = 0

        return [time_value, beerTemp, fridgeTemp]

# A model representing the fermentation profile as a whole
class FermentationProfile(models.Model):
    STATUS_ACTIVE = 1
    STATUS_PENDING_DELETE = 2

    STATUS_CHOICES = (
        (STATUS_ACTIVE, 'Active'),
        (STATUS_PENDING_DELETE, 'Pending Delete'),
    )

    name = models.CharField(max_length=128)
    status = models.IntegerField(choices=STATUS_CHOICES, default=STATUS_ACTIVE)

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
        # TODO - Make this temperature format sensitive
        profile_points = self.fermentationprofilepoint_set.order_by('ttl')

        description = []
        past_first_point=False  # There's guaranteed to be a better way to do this
        previous_setpoint = 0.0
        previous_ttl = 0.0
        previous_format = 'F'  #

        if profile_points.__len__() < 1:
            description.append("This profile contains no setpoints and cannot be assigned.")

        # TODO - Make the timedelta objects more human readable (I don't like the 5:20:30 format that much)
        for this_point in profile_points:
            if not past_first_point:
                desc_text = "Start off by heating/cooling to {} degrees {}".format(this_point.temperature_setting, this_point.temp_format)

                if this_point.ttl == 0:  # TODO - Test to make sure this works with timedelta objects the way I think it does
                    desc_text += "."
                else:
                    desc_text += " and hold this temperature for {}".format(this_point.ttl)

                description.append(desc_text)
                previous_setpoint = this_point.temperature_setting
                previous_ttl = this_point.ttl
                past_first_point = True
                previous_format = this_point.temp_format
            else:
                if previous_setpoint == this_point.temperature_setting:
                    desc_text = "Hold this temperature for {}".format((this_point.ttl - previous_ttl))
                    desc_text += "(until {} after the profile was assigned).".format(this_point.ttl)
                else:
                    if previous_setpoint > this_point.temperature_setting:
                        desc_text = "Cool to"
                    else:  # If previous_setpoint is less than the current setpoint
                        desc_text = "Heat to"

                    # Breaking this up to reduce line length
                    desc_text += " {} degrees {} ".format(this_point.temperature_setting, this_point.temp_format)
                    desc_text += "over the next {} ".format(this_point.ttl - previous_ttl)
                    desc_text += "(reaching this temperature {}".format(this_point.ttl)
                    desc_text += " after the profile was assigned)."

                description.append(desc_text)
                previous_setpoint = this_point.temperature_setting
                previous_ttl = this_point.ttl
                previous_format = this_point.temp_format

        if past_first_point:
            desc_text = "Finally, permanently hold the temperature at {} degrees {}.".format(previous_setpoint, previous_format)
            description.append(desc_text)

        return description

    # profile_temp replaces brewpi-script/temperatureProfile.py, and is intended to be called by
    # get_profile_temp from BrewPiDevice
    def profile_temp(self, time_started):
        # TODO - Make this temperature format sensitive
        profile_points = self.fermentationprofilepoint_set.order_by('ttl')

        past_first_point=False  # There's guaranteed to be a better way to do this
        previous_setpoint = 0.0
        previous_ttl = 0.0
        previous_format = 'F'
        timezone_obj = pytz.timezone(getattr(settings, 'TIME_ZONE', 'UTC'))
        current_time = datetime.datetime.now(tz=timezone_obj)

        for this_point in profile_points:
            # TODO - Refactor this at some point
            if not past_first_point:
                # If we haven't hit the first TTL yet, we are in the initial lag period where we hold a constant
                # temperature. Return the temperature setting
                if current_time < (time_started + this_point.ttl):
                    return this_point.temperature_setting
                past_first_point = True
            else:
                # Test if we are in this period
                if current_time < (time_started + this_point.ttl):
                    # We are - Check if we need to interpolate, or if we can just use the static temperature
                    if this_point.temperature_setting == previous_setpoint:  # We can just use the static temperature
                        return this_point.temperature_setting
                    else:  # We have to interpolate
                        duration = this_point.ttl.total_seconds() - previous_ttl.total_seconds()
                        delta = (this_point.temperature_setting - previous_setpoint)
                        slope = float(delta) / duration

                        seconds_into_point = (current_time - (time_started + previous_ttl)).total_seconds()

                        return round(seconds_into_point * slope + float(previous_setpoint), 1)

            previous_setpoint = this_point.temperature_setting
            previous_ttl = this_point.ttl
            previous_format = this_point.temp_format

        # If we hit this point, we looped through all the setpoints & aren't between two (or on the first one)
        # That is to say - we're at the end. Just return the last setpoint.
        return previous_setpoint



class FermentationProfilePoint(models.Model):
    TEMP_FORMAT_CHOICES = (('C', 'Celsius'), ('F', 'Fahrenheit'))

    profile = models.ForeignKey(FermentationProfile)
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
        # Check Constance
        if config.TEMPERATURE_FORMAT == 'F':
            return self.temp_to_f()
        elif config.TEMPERATURE_FORMAT == 'C':
            return self.temp_to_c()
        pass


# The old (0.2.x/Arduino) Control Constants Model
# TODO - Update all usages of the ControlConstants objects to add 'controller' when the object is created
class OldControlConstants(models.Model):
    # TODO - Check that verbose_names and descriptions are ok
    tempSetMin = models.FloatField(
        verbose_name="Min Temperature",
        help_text="The fridge and beer temperatures cannot go below this value"
        )
    tempSetMax = models.FloatField(
        verbose_name="Max Temperature",
        help_text="The fridge and beer temperatures cannot go above this value"
        )
    Kp = models.FloatField(
        verbose_name="PID: Kp",
        help_text="The beer temperature error is multiplied by " \
                  "Kp to give the proportional of the PID value"
        )
    Ki = models.FloatField(
        verbose_name="PID: Ki",
        help_text="When the intergral is active, the error is added" \
                  "to the integral every 30 sec. The result is multiplied" \
                  "by Ki to give the integral part"
        )
    Kd = models.FloatField(
        verbose_name="PID: Kd",
        help_text="The derivative of the beer temperature is multiplied by " \
                  "Kd to give the derivative part of the PID value."
        )
    pidMax = models.FloatField(
        verbose_name="PID: maximum",
        help_text="Defines the maximum difference between the beer temp " \
                  "setting and fridge temp setting. The fridge setting " \
                  "will be clipped to this range."
        )
    iMaxErr = models.FloatField(
        verbose_name="Integrator: Max temp error C",
        help_text="The integral is only active when the temperature is " \
                  "close to the target temperature. This is the maximum "\
                  "error for which the integral is active"
    )
    idleRangeH = models.FloatField(
        verbose_name="Temperature idle range top",
        help_text="When the fridge temperature is within this range, it " \
                  "will not heat or cool, regardless of other setting."
    )
    idleRangeL = models.FloatField(
        verbose_name="Temperature idle range bottom",
        help_text="When the fridge temperature is within this range, it " \
                  "will not heat or cool, regardless of other setting."
    )
    heatTargetH = models.FloatField(
        verbose_name="Heating target upper bound",
        help_text="When the overshoot lands under this value, the peak " \
                   "is within target range and the estimator is not adjusted"
    )
    heatTargetL = models.FloatField(
        verbose_name="Heating target lower bound",
        help_text="When the overshoot lands above this value, the peak " \
                   "is within target range and the estimator is not adjusted"
    )
    coolTargetH = models.FloatField(
        verbose_name="Cooling target upper bound",
        help_text="When the overshoot lands under this value, the peak " \
                   "is within target range and the estimator is not adjusted"
    )
    coolTargetL = models.FloatField(
        verbose_name="Cooling target lower bound",
        help_text="When the overshoot lands above this value, the peak " \
                   "is within target range and the estimator is not adjusted"

    )

    maxHeatTimeForEst = models.FloatField(
        verbose_name="Maximum time in seconds for heating overshoot estimator",
        help_text="The time the fridge has been heating is used to estimate overshoot. "\
                  "This is the maximum time that is tahen into account"
    )
    maxCoolTimeForEst = models.FloatField(
        verbose_name="Maximum time in seconds for cooling overshoot estimator",
        help_text="Maximum time the frige has been cooling is used to estimate " \
                  "overshoot. This is the maximum time that is taken into account"
    )
    beerFastFilt = models.FloatField(
        verbose_name="Beer fast filter delay time",
        help_text="The beer fast filter is used for display and data logging. " \
                  "More filtering give a smoother line but also more delay"
    )
    beerSlowFilt = models.FloatField(
        verbose_name="Beer slow filter delay time",
        help_text="The beer slow filter is used for the control algorithm. " \
                  "The frige temperature setting is calculated from this filter. " \
                  "Because a small difference in beer temperature cases a large " \
                  "adjustment in the fridge temperature, more smoothing is needed"
    )
    beerSlopeFilt = models.FloatField(
        verbose_name="Beer slope filter delay time",
        help_text="The slope is calculated every 30 sec and fed to this filter. " \
                  "More filtering means a smoother frige setting."
    )
    fridgeFastFilt = models.FloatField(
        verbose_name="Fridge fast filter delay time",
        help_text="The fridge fast filter is used for on-off control, display " \
                  "and logging. It needs to have a small delay."
    )
    fridgeSlowFilt = models.FloatField(
        verbose_name="Fridge slow filter delay time",
        help_text="The fridge slow filter is used for peak detection to adjust " \
                  "the overshoot estimators. More smoothing is needed to prevent " \
                  "small fluctiations to be recognized as peaks."
    )
    fridgeSlopeFilt = models.FloatField(
        verbose_name="Fidlge slope filter delay time",
        help_text="Not used?"
    )

    lah = models.FloatField(
        verbose_name="Use light as heater?",
        help_text="If this options is set to Yes the light will be used as a heater",
        choices=(
            ("Y", "YES"),
            ("N", "No")
        ),
        default="N"
    )
    # TODO - verbose_name and help_text
    hs = models.FloatField()

    tempFormat = models.CharField(
        verbose_name="Temperature format",
        max_length=1,
        choices=(
            ("F", "Farenheit"),
            ("C", "Celcius")
        ),
        default='F'
        )

    # In a lot of cases we're selectively loading/sending/comparing the fields that are known by the firmware
    # To make it easy to iterate over those fields, going to list them out here
    firmware_field_list = ['tempSetMin', 'tempSetMax', 'Kp', 'Ki', 'Kd', 'pidMax', 'iMaxErr', 'idleRangeH',
                           'idleRangeL', 'heatTargetH', 'heatTargetL', 'coolTargetH', 'coolTargetL',
                           'maxHeatTimeForEst', 'maxCoolTimeForEst', 'beerFastFilt', 'beerSlowFilt', 'beerSlopeFilt',
                           'fridgeFastFilt', 'fridgeSlowFilt', 'fridgeSlopeFilt', 'lah', 'hs', 'tempFormat']

    controller = models.ForeignKey(BrewPiDevice)  # TODO - Determine if this is used anywhere (other than below) and if we want to keep it.

    # preset_name is only used if we want to save the preset to the database to be reapplied later
    preset_name = models.CharField(max_length=255, null=True, blank=True, default="")


    def load_from_controller(self, controller=None):
        """
        :param controller: models.BrewPiDevice
        :type controller: BrewPiDevice
        :return: boolean
        """
        if controller is not None:
            self.controller = controller

        try:
            cc = json.loads(self.controller.send_and_receive_from_socket("getControlConstants"))

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
        return controller.send_message("setParameters", json.dumps(value_to_send))

    def save_all_to_controller(self, controller, prior_control_constants=None):
        """
        :param controller: models.BrewPiDevice
        :type controller: BrewPiDevice
        :return: boolean
        """
        for this_field in self.firmware_field_list:
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

    controller = models.ForeignKey(BrewPiDevice)

    # preset_name is only used if we want to save the preset to the database to be reapplied later
    preset_name = models.CharField(max_length=255, null=True, blank=True, default="")

    # In a lot of cases we're selectively loading/sending/comparing the fields that are known by the firmware
    # To make it easy to iterate over those fields, going to list them out here
    firmware_field_list = ['tempFormat', 'heater1_kp', 'heater1_ti', 'heater1_td', 'heater1_infilt', 'heater1_dfilt',
                           'iMaxErr', 'idleRangeH',
                           'idleRangeL', 'heatTargetH', 'heatTargetL', 'coolTargetH', 'coolTargetL',
                           'maxHeatTimeForEst', 'maxCoolTimeForEst', 'beerFastFilt', 'beerSlowFilt', 'beerSlopeFilt',
                           'fridgeFastFilt', 'fridgeSlowFilt', 'fridgeSlopeFilt', 'lah', 'hs',]
    # TODO - Update the above


    def load_from_controller(self, controller):
        """
        :param controller: models.BrewPiDevice
        :type controller: BrewPiDevice
        :return: boolean
        """
        try:
            cc = json.loads(controller.send_and_receive_from_socket("getControlConstants"))

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

        value_to_send = {attribute, getattr(self, attribute)}
        return controller.send_message("setParameters", json.dumps(value_to_send))

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
#             cc = json.loads(self.controller.send_and_receive_from_socket("getControlSettings"))
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
