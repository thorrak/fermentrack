from __future__ import unicode_literals

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

import socket
import json, time, datetime


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


class InstallSettings(models.Model):
    """
    This is going to be a singleton object to hold the installation settings. There may be a better way to do this...
    """

    DATE_TIME_FORMAT_DISPLAY_CHOICES = (
        ("mm/dd/yy", "mm/dd/yy"),
        ("dd/mm/yy", "dd/mm/yy"),
    )

    brewery_name = models.CharField(max_length=25, default="BrewPi-Django", help_text="Name to be displayed in the upper left of each page")
    # TODO - Determine if date_time_format is used anywhere
    date_time_format = models.CharField(max_length=20, default="yy-mm-dd", null=False, blank=False)
    date_time_format_display = models.CharField(max_length=20, default="mm/dd/yy", choices=DATE_TIME_FORMAT_DISPLAY_CHOICES,
                                                null=False, blank=False)
    require_login_for_dashboard = models.BooleanField(default=False, help_text="Should a logged out user be able to see device status?")


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

    pin_data = models.ForeignKey(PinDevice, null=True, blank=True, default=None)

    controller = models.ForeignKey('BrewPiDevice', null=True, default=None)

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
        if address is not None:
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

#    active_beer = models.ForeignKey()

    device_name = models.CharField(max_length=48, help_text="Unique name for this device", unique=True)

    # This is set at the device level, and should probably be read from the device as well. Going to include here
    # to cache it.
    temp_format = models.CharField(max_length=1, choices=TEMP_FORMAT_CHOICES, default='C', help_text="Temperature units")

    data_point_log_interval = models.IntegerField(default=10, choices=DATA_POINT_TIME_CHOICES,
                                                  help_text="Time between logged data points")

    has_old_brewpi_www = models.BooleanField(default=True, help_text="Does this device also have the old-style " +
                                                                     "(PHP-based) brewpi-www installed somewhere?")

    ######## The following are used if we are loading the configuration directly from the database.
    # TODO - I really should try to eliminate wwwPath wherever possible (we're no longer going to allow linking back to it)
    wwwPath = models.CharField(max_length=255, help_text="Path to the BrewPi-www installation (deprecated??)",
                               default="/var/www")
    useInetSocket = models.BooleanField(default=False, help_text="Whether or not to use an internet socket (rather than local)")
    socketPort = models.IntegerField(default=2222, validators=[MinValueValidator(10,"Port must be 10 or higher"),
                                                               MaxValueValidator(65535, "Port must be 65535 or lower")],
                                     help_text="The internet socket to use (only used if useInetSocket above is "
                                               "\"True\")")
    socketHost = models.CharField(max_length=128, default="localhost", help_text="The interface to bind for the "
                                                                                 "internet socket (only used if "
                                                                                 "useInetSocket above is \"True\")")
    logging_status = models.CharField(max_length=10, choices=DATA_LOGGING_CHOICES, default='stopped', help_text="Data logging status")
    # TODO - Determine if script_path can be eliminated given we are using a custom brewpi-script
    script_path = models.CharField(max_length=255, help_text="Path to the BrewPi script (deprecated??)",
                                   default="/home/brewpi/")

    serial_port = models.CharField(max_length=255, help_text="Serial port to which the BrewPi device is connected",
                                   default="auto")
    serial_alt_port = models.CharField(max_length=255, help_text="Alternate serial port to which the BrewPi device is connected (??)",
                                   default="None")
    board_type = models.CharField(max_length=10, default="uno", choices=BOARD_TYPE_CHOICES, help_text="Board type to which BrewPi is connected")

    # TODO - Add some kind of helper function to test if process_id is valid, and reset to 0 if it is not.
    process_id = models.IntegerField(default=0)
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
            time.sleep(5)  # This is a horrible practice, and I feel dirty just writing it.
            device_response = self.send_and_receive_from_socket("getDeviceList")
            loop_number += 1

        if not device_response:
            # TODO - Modify this to return an actual error message
            return None
        elif device_response == "device-list-not-up-to-date":
            # TODO - Modify this to return an actual error message
            return None

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

        return True




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


class FermentationProfilePoint(models.Model):
    TEMP_FORMAT_CHOICES = (('C', 'Celsius'), ('F', 'Fahrenheit'))

    profile = models.ForeignKey(FermentationProfile)
    ttl = models.DurationField(help_text="Time at which we should arrive at this temperature")
    temperature_setting = models.DecimalField(max_digits=5, decimal_places=2, null=True,
                                              help_text="The temperature the beer should be when TTL has passed")
    temp_format = models.CharField(max_length=1, default='F')


# The old (0.2.x/Arduino) Control Constants Model
class OldControlConstants(models.Model):
    # class Meta:
    #     managed = False

    tempSetMin = models.FloatField()
    tempSetMax = models.FloatField()
    Kp = models.FloatField()
    Ki = models.FloatField()
    Kd = models.FloatField()
    pidMax = models.FloatField()
    iMaxErr = models.FloatField()
    idleRangeH = models.FloatField()
    idleRangeL = models.FloatField()
    heatTargetH = models.FloatField()
    heatTargetL = models.FloatField()
    coolTargetH = models.FloatField()
    coolTargetL = models.FloatField()

    maxHeatTimeForEst = models.FloatField()
    maxCoolTimeForEst = models.FloatField()
    beerFastFilt = models.FloatField()
    beerSlowFilt = models.FloatField()
    beerSlopeFilt = models.FloatField()
    fridgeFastFilt = models.FloatField()
    fridgeSlowFilt = models.FloatField()
    fridgeSlopeFilt = models.FloatField()

    lah = models.FloatField()
    hs = models.FloatField()

    # In a lot of cases we're selectively loading/sending/comparing the fields that are known by the firmware
    # To make it easy to iterate over those fields, going to list them out here
    firmware_field_list = ['tempSetMin', 'tempSetMax', 'Kp', 'Ki', 'Kd', 'pidMax', 'iMaxErr', 'idleRangeH',
                           'idleRangeL', 'heatTargetH', 'heatTargetL', 'coolTargetH', 'coolTargetL',
                           'maxHeatTimeForEst', 'maxCoolTimeForEst', 'beerFastFilt', 'beerSlowFilt', 'beerSlopeFilt',
                           'fridgeFastFilt', 'fridgeSlowFilt', 'fridgeSlopeFilt', 'lah', 'hs',]


    controller = models.ForeignKey(BrewPiDevice)

    # preset_name is only used if we want to save the preset to the database to be reapplied later
    preset_name = models.CharField(max_length=255, null=True, blank=True, default="")


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




# The old (0.2.x/Arduino) Control Constants Model
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

