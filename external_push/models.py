from __future__ import unicode_literals

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

import requests
import logging

import json

from app.models import BrewPiDevice
from gravity.models import GravitySensor


class GenericPushTarget(models.Model):
    class Meta:
        verbose_name = "Generic Push Target"
        verbose_name_plural = "Generic Push Targets"

    SENSOR_SELECT_ALL = "all"
    SENSOR_SELECT_LIST = "list"
    SENSOR_SELECT_NONE = "none"

    SENSOR_SELECT_CHOICES = (
        (SENSOR_SELECT_ALL, "All Active Sensors/Devices"),
        (SENSOR_SELECT_LIST, "Specific Sensors/Devices"),
        (SENSOR_SELECT_NONE, "Nothing of this type"),
    )

    SENSOR_PUSH_HTTP = "http (post)"
    SENSOR_PUSH_TCP = "tcp"

    SENSOR_PUSH_CHOICES = (
        (SENSOR_PUSH_HTTP, "HTTP/HTTPS"),
        (SENSOR_PUSH_TCP, "TCP (Telnet/Socket)"),
    )

    STATUS_ACTIVE = 'active'
    STATUS_DISABLED = 'disabled'
    STATUS_ERROR = 'error'

    STATUS_CHOICES = (
        (STATUS_ACTIVE, 'Active'),
        (STATUS_DISABLED, 'Disabled'),
        (STATUS_ERROR, 'Error'),
    )

    DATA_FORMAT_GENERIC = 'generic'
    DATA_FORMAT_TILTBRIDGE = 'tiltbridge'

    DATA_FORMAT_CHOICES = (
        (DATA_FORMAT_GENERIC, 'All Data (Generic)'),
        # (DATA_FORMAT_TILTBRIDGE, 'TiltBridge Device'),
    )

    PUSH_FREQUENCY_CHOICES = (
        # (30-1,    '30 seconds'),
        (60-1,    '1 minute'),
        (60*2-1,  '2 minutes'),
        (60*5-1,  '5 minutes'),
        (60*10-1, '10 minutes'),
        (60*15-1, '15 minutes'),
        (60*30-1, '30 minutes'),
        (60*60-1, '1 hour'),
    )

    name = models.CharField(max_length=48, help_text="Unique name for this push target", unique=True)
    status = models.CharField(max_length=24, help_text="Status of this push target", choices=STATUS_CHOICES,
                              default=STATUS_ACTIVE)
    push_frequency = models.IntegerField(choices=PUSH_FREQUENCY_CHOICES, default=60*15,
                                         help_text="How often to push data to the target")
    api_key = models.CharField(max_length=256, help_text="API key required by the push target (if any)", default="",
                               blank=True)

    brewpi_push_selection = models.CharField(max_length=12, choices=SENSOR_SELECT_CHOICES, default=SENSOR_SELECT_ALL,
                                             help_text="How the BrewPi devices to push are selected")
    brewpi_to_push = models.ManyToManyField(to=BrewPiDevice, related_name="push_targets", blank=True, default=None,
                                            help_text="BrewPi Devices to push (ignored if 'all' devices selected)")

    gravity_push_selection = models.CharField(max_length=12, choices=SENSOR_SELECT_CHOICES, default=SENSOR_SELECT_ALL,
                                              help_text="How the gravity sensors to push are selected")
    gravity_sensors_to_push = models.ManyToManyField(to=GravitySensor, related_name="push_targets", blank=True, default=None,
                                                     help_text="Gravity Sensors to push (ignored if 'all' "
                                                               "sensors selected)")

    target_type = models.CharField(max_length=24, default=SENSOR_PUSH_HTTP, choices=SENSOR_PUSH_CHOICES,
                                   help_text="Protocol to use to connect to the push target")
    # TODO - Change default to "", and change the URL to be a placeholder on the form
    target_host = models.CharField(max_length=256, default="http://127.0.0.1/", blank=True,
                                   help_text="The URL to push to (for HTTP/HTTPS) or hostname/IP address (for TCP)")
    target_port = models.IntegerField(default=80, validators=[MinValueValidator(10,"Port must be 10 or higher"),
                                                              MaxValueValidator(65535, "Port must be 65535 or lower")],
                                      help_text="The port to use (not used for HTTP/HTTPS)")

    data_format = models.CharField(max_length=24, help_text="The data format to send to the push target",
                                   choices=DATA_FORMAT_CHOICES, default=DATA_FORMAT_GENERIC)

    error_text = models.TextField(blank=True, null=True, default="", help_text="The error (if any) encountered on the "
                                                                               "last push attempt")

    last_triggered = models.DateTimeField(help_text="The last time we pushed data to this target", auto_now_add=True)

    # I'm on the fence as to whether or not to test when to trigger by selecting everything from the database and doing
    # (last_triggered + push_frequency) < now, or to actually create a "trigger_next_at" field.
    # trigger_next_at = models.DateTimeField(default=timezone.now, help_text="When to next trigger a push")

    def data_to_push(self):
        if self.brewpi_push_selection == GenericPushTarget.SENSOR_SELECT_ALL:
            brewpi_to_send = BrewPiDevice.objects.filter(status=BrewPiDevice.STATUS_ACTIVE)
        elif self.brewpi_push_selection == GenericPushTarget.SENSOR_SELECT_LIST:
            brewpi_to_send = self.brewpi_to_push.all()
        else:
            # Either SENSOR_SELECT_NONE or not implemented yet
            brewpi_to_send = None

        if self.gravity_push_selection == GenericPushTarget.SENSOR_SELECT_ALL:
            grav_sensors_to_send = GravitySensor.objects.filter(status=GravitySensor.STATUS_ACTIVE)
        elif self.gravity_push_selection == GenericPushTarget.SENSOR_SELECT_LIST:
            grav_sensors_to_send = self.gravity_sensors_to_push.all()
        else:
            grav_sensors_to_send = None

        # At this point we've obtained the list of objects to send - now we just need to format them.
        string_to_send = ""  # This is what ultimately needs to be populated.
        if self.data_format == self.DATA_FORMAT_TILTBRIDGE:
            to_send = {'api_key': self.api_key, 'brewpi': []}
            if brewpi_to_send is not None:
                for brewpi in brewpi_to_send:
                    # TODO - Handle this if the brewpi can't be loaded, given "get_dashpanel_info" communicates with BrewPi-Script
                    # TODO - Make it so that this data is stored in/loaded from Redis
                    device_info = brewpi.get_dashpanel_info()

                    data_to_send = {
                        'name': brewpi.device_name,
                        'internal_id': brewpi.id,
                        'temp_format': brewpi.temp_format,
                    }

                    # Because not every device will have temp sensors, only serialize the sensors that exist.
                    # Have to coerce temps to floats, as Decimals aren't json serializable
                    if device_info['BeerTemp'] is not None:
                        data_to_send['beer_temp'] = float(device_info['BeerTemp'])
                    if device_info['FridgeTemp'] is not None:
                        data_to_send['fridge_temp'] = float(device_info['FridgeTemp'])

                    # Gravity isn't retrieved via get_dashpanel_info, and as such requires special handling
                    try:
                        if brewpi.gravity_sensor is not None:
                            gravity = brewpi.gravity_sensor.retrieve_latest_gravity()
                            if gravity is not None:
                                data_to_send['gravity'] = float(gravity)
                    except:
                        pass

                    to_send['brewpi'].append(data_to_send)

            string_to_send = json.dumps(to_send)

        elif self.data_format == self.DATA_FORMAT_GENERIC:
            GENERIC_DATA_FORMAT_VERSION = "1.0"

            to_send = {'api_key': self.api_key, 'version': GENERIC_DATA_FORMAT_VERSION, 'brewpi_devices': [],
                       'gravity_sensors': []}
            if brewpi_to_send is not None:
                for brewpi in brewpi_to_send:
                    # TODO - Make it so that this data is stored in/loaded from Redis
                    device_info = brewpi.get_dashpanel_info()

                    if device_info is None:
                        continue

                    # Have to coerce temps to floats, as Decimals aren't json serializable
                    data_to_send = {
                        'name': brewpi.device_name,
                        'internal_id': brewpi.id,
                        'temp_format': brewpi.temp_format,
                        'control_mode': device_info['Mode'],  # TODO - Determine if we want the raw or verbose device mode
                    }

                    # Because not every device will have temp sensors, only serialize the sensors that exist.
                    # Have to coerce temps to floats, as Decimals aren't json serializable
                    if device_info['BeerTemp'] is not None:
                        if device_info['BeerTemp'] != 0:
                            data_to_send['beer_temp'] = float(device_info['BeerTemp'])
                    if device_info['FridgeTemp'] is not None:
                        if device_info['FridgeTemp'] != 0:
                            data_to_send['fridge_temp'] = float(device_info['FridgeTemp'])
                    if device_info['RoomTemp'] is not None:
                        if device_info['RoomTemp'] != 0:
                            data_to_send['room_temp'] = float(device_info['RoomTemp'])

                    # Gravity isn't retrieved via get_dashpanel_info, and as such requires special handling
                    try:
                        if brewpi.gravity_sensor is not None:
                            gravity = brewpi.gravity_sensor.retrieve_latest_gravity()
                            if gravity is not None:
                                data_to_send['gravity'] = float(gravity)
                    except:
                        pass

                    to_send['brewpi_devices'].append(data_to_send)

            if grav_sensors_to_send is not None:
                for sensor in grav_sensors_to_send:
                    grav_dict = {
                        'name': sensor.name,
                        'internal_id': sensor.id,
                        'sensor_type': sensor.sensor_type,
                    }

                    latest_log_point = sensor.retrieve_latest_point()
                    if latest_log_point is not None:
                        # For now, if we can't get a latest log point, let's default to just not sending anything.
                        if latest_log_point.gravity != 0.0:
                            grav_dict['gravity'] = float(latest_log_point.gravity)

                        # For now all gravity sensors have temp info, but just in case
                        if latest_log_point.temp is not None:
                            grav_dict['temp'] = float(latest_log_point.temp)
                            grav_dict['temp_format'] = latest_log_point.temp_format

                    to_send['gravity_sensors'].append(grav_dict)

            string_to_send = json.dumps(to_send)

        else:
            raise ValueError("Invalid data format specified for push target")
        # We've got the data (in a json'ed string) - lets send it
        return string_to_send

    def send_data(self):
        # self.data_to_push() returns a JSON-encoded string which we will push directly out
        json_data = self.data_to_push()

        if len(json_data) <= 0:
            # There was no data to push - do nothing.
            return False

        if self.target_type == self.SENSOR_PUSH_HTTP:
            r = requests.post(self.target_host, data=json_data)
            return True  # TODO - Check if the post actually succeeded & react accordingly
        elif self.target_type == self.SENSOR_PUSH_TCP:
            # TODO - Push to a socket endpoint
            raise NotImplementedError("TCP push targets (sockets) are not yet implemented")
        else:
            raise ValueError("Invalid target type specified for push target")

        return False  # Should never get here, but just in case something changes later


class BrewersFriendPushTarget(models.Model):
    class Meta:
        verbose_name = "Brewers Friend Push Target"
        verbose_name_plural = "Brewers Friend Push Targets"

    STATUS_ACTIVE = 'active'
    STATUS_DISABLED = 'disabled'
    STATUS_ERROR = 'error'

    STATUS_CHOICES = (
        (STATUS_ACTIVE, 'Active'),
        (STATUS_DISABLED, 'Disabled'),
        (STATUS_ERROR, 'Error'),
    )

    PUSH_FREQUENCY_CHOICES = (
        # (30-1,    '30 seconds'),
        (60 - 1, '1 minute'),
        (60 * 2 - 1, '2 minutes'),
        (60 * 5 - 1, '5 minutes'),
        (60 * 10 - 1, '10 minutes'),
        (60 * 15 - 1, '15 minutes'),
        (60 * 30 - 1, '30 minutes'),
        (60 * 60 - 1, '1 hour'),
    )

    status = models.CharField(max_length=24, help_text="Status of this push target", choices=STATUS_CHOICES,
                              default=STATUS_ACTIVE)
    push_frequency = models.IntegerField(choices=PUSH_FREQUENCY_CHOICES, default=60 * 15,
                                         help_text="How often to push data to the target")
    api_key = models.CharField(max_length=256, help_text="Brewers Friend API Key", default="")

    gravity_sensor_to_push = models.ForeignKey(to=GravitySensor, related_name="brewers_friend_push_target", on_delete=models.CASCADE,
                                               help_text="Gravity Sensor to push (create one push target per "
                                                         "sensor to push)")

    error_text = models.TextField(blank=True, null=True, default="", help_text="The error (if any) encountered on the "
                                                                               "last push attempt")

    last_triggered = models.DateTimeField(help_text="The last time we pushed data to this target", auto_now_add=True)

    # I'm on the fence as to whether or not to test when to trigger by selecting everything from the database and doing
    # (last_triggered + push_frequency) < now, or to actually create a "trigger_next_at" field.
    # trigger_next_at = models.DateTimeField(default=timezone.now, help_text="When to next trigger a push")

    def __str__(self):
        return self.gravity_sensor_to_push.name

    def data_to_push(self):
        # For Brewers Friend, we're just cascading a single gravity sensor downstream to the app
        to_send = {'report_source': "Fermentrack", 'name': self.gravity_sensor_to_push.name}

        if self.gravity_sensor_to_push.sensor_type == GravitySensor.SENSOR_TILT:
            to_send['device_source'] = "Tilt"
        elif self.gravity_sensor_to_push.sensor_type == GravitySensor.SENSOR_ISPINDEL:
            to_send['device_source'] = "iSpindel"
        elif self.gravity_sensor_to_push.sensor_type == GravitySensor.SENSOR_MANUAL:
            to_send['device_source'] = "Manual"
        else:
            to_send['device_source'] = "Unknown"


        latest_log_point = self.gravity_sensor_to_push.retrieve_latest_point()

        if latest_log_point is None:  # If there isn't an available log point, return nothing
            return {}

        # For now, if we can't get a latest log point, let's default to just not sending anything.
        if latest_log_point.gravity != 0.0:
            to_send['gravity'] = float(latest_log_point.gravity)
            to_send['gravity_unit'] = "G"
        else:
            return {}  # Also return nothing if there isn't an available gravity

        # For now all gravity sensors have temp info, but just in case
        if latest_log_point.temp is not None:
            to_send['temp'] = float(latest_log_point.temp)
            to_send['temp_unit'] = latest_log_point.temp_format

        string_to_send = json.dumps(to_send)

        # We've got the data (in a json'ed string) - lets send it
        return string_to_send

    def send_data(self):
        # self.data_to_push() returns a JSON-encoded string which we will push directly out
        json_data = self.data_to_push()

        if len(json_data) <= 2:
            # There was no data to push - do nothing.
            return False

        headers = {'Content-Type': 'application/json', 'X-API-KEY': self.api_key}
        brewers_friend_url = "https://log.brewersfriend.com/stream/" + self.api_key

        r = requests.post(brewers_friend_url, data=json_data, headers=headers)
        return True  # TODO - Check if the post actually succeeded & react accordingly



class BrewfatherPushTarget(models.Model):
    class Meta:
        verbose_name = "Brewfather Push Target"
        verbose_name_plural = "Brewfather Push Targets"

    STATUS_ACTIVE = 'active'
    STATUS_DISABLED = 'disabled'
    STATUS_ERROR = 'error'

    STATUS_CHOICES = (
        (STATUS_ACTIVE, 'Active'),
        (STATUS_DISABLED, 'Disabled'),
        (STATUS_ERROR, 'Error'),
    )

    PUSH_FREQUENCY_CHOICES = (
        (60 * 15 + 1, '15 minutes'),
        (60 * 30 + 1, '30 minutes'),
        (60 * 60 + 1, '1 hour'),
    )

    status = models.CharField(max_length=24, help_text="Status of this push target", choices=STATUS_CHOICES,
                              default=STATUS_ACTIVE)
    push_frequency = models.IntegerField(choices=PUSH_FREQUENCY_CHOICES, default=60 * 15,
                                         help_text="How often to push data to the target")
    logging_url = models.CharField(max_length=256, help_text="Brewfather Logging URL", default="")

    gravity_sensor_to_push = models.ForeignKey(to=GravitySensor, related_name="brewfather_push_target", on_delete=models.CASCADE,
                                               help_text="Gravity Sensor to push (create one push target per "
                                                         "sensor to push)")

    error_text = models.TextField(blank=True, null=True, default="", help_text="The error (if any) encountered on the "
                                                                               "last push attempt")

    last_triggered = models.DateTimeField(help_text="The last time we pushed data to this target", auto_now_add=True)

    # I'm on the fence as to whether or not to test when to trigger by selecting everything from the database and doing
    # (last_triggered + push_frequency) < now, or to actually create a "trigger_next_at" field.
    # trigger_next_at = models.DateTimeField(default=timezone.now, help_text="When to next trigger a push")

    def __str__(self):
        return self.gravity_sensor_to_push.name

    def data_to_push(self):
        # For Brewfather, we're just cascading a single gravity sensor downstream to the app
        to_send = {'report_source': "Fermentrack", 'name': self.gravity_sensor_to_push.name}

        # TODO - Add beer name to what is pushed

        latest_log_point = self.gravity_sensor_to_push.retrieve_latest_point()

        if latest_log_point is None:  # If there isn't an available log point, return nothing
            return {}

        # For now, if we can't get a latest log point, let's default to just not sending anything.
        if latest_log_point.gravity != 0.0:
            to_send['gravity'] = float(latest_log_point.gravity)
            to_send['gravity_unit'] = "G"
        else:
            return {}  # Also return nothing if there isn't an available gravity

        # For now all gravity sensors have temp info, but just in case
        if latest_log_point.temp is not None:
            to_send['temp'] = float(latest_log_point.temp)
            to_send['temp_unit'] = latest_log_point.temp_format

        # TODO - Add linked BrewPi temps if we have them

        string_to_send = json.dumps(to_send)

        # We've got the data (in a json'ed string) - lets send it
        return string_to_send

    def send_data(self):
        # self.data_to_push() returns a JSON-encoded string which we will push directly out
        json_data = self.data_to_push()

        if len(json_data) <= 2:
            # There was no data to push - do nothing.
            return False

        headers = {'Content-Type': 'application/json'}

        r = requests.post(self.logging_url, data=json_data, headers=headers)
        return True  # TODO - Check if the post actually succeeded & react accordingly

class GrainfatherPushTarget(models.Model):
    class Meta:
        verbose_name = "Grainfather Push Target"
        verbose_name_plural = "Grainfather Push Targets"

    STATUS_ACTIVE = 'active'
    STATUS_DISABLED = 'disabled'
    STATUS_ERROR = 'error'

    STATUS_CHOICES = (
        (STATUS_ACTIVE, 'Active'),
        (STATUS_DISABLED, 'Disabled'),
        (STATUS_ERROR, 'Error'),
    )

    PUSH_FREQUENCY_CHOICES = (
        (60 * 15 + 1, '15 minutes'),
        (60 * 30 + 1, '30 minutes'),
        (60 * 60 + 1, '1 hour'),
    )

    status = models.CharField(max_length=24, help_text="Status of this push target", choices=STATUS_CHOICES,
                              default=STATUS_ACTIVE)
    push_frequency = models.IntegerField(choices=PUSH_FREQUENCY_CHOICES, default=60 * 15,
                                         help_text="How often to push data to the target")
    logging_url = models.CharField(max_length=256, help_text="Grainfather Logging URL", default="")

    gravity_sensor_to_push = models.ForeignKey(to=GravitySensor, related_name="grainfather_push_target", on_delete=models.CASCADE,
                                               help_text="Gravity Sensor to push (create one push target per "
                                                         "sensor to push)")

    error_text = models.TextField(blank=True, null=True, default="", help_text="The error (if any) encountered on the "
                                                                               "last push attempt")

    last_triggered = models.DateTimeField(help_text="The last time we pushed data to this target", auto_now_add=True)

    # I'm on the fence as to whether or not to test when to trigger by selecting everything from the database and doing
    # (last_triggered + push_frequency) < now, or to actually create a "trigger_next_at" field.
    # trigger_next_at = models.DateTimeField(default=timezone.now, help_text="When to next trigger a push")

    def __str__(self):
        return self.gravity_sensor_to_push.name

    def data_to_push(self):
        # For Grainfather, we're just cascading a single gravity sensor downstream to the app
        to_send = {'report_source': "Fermentrack", 'name': self.gravity_sensor_to_push.name, 'token':"grainfather", 'ID':"",'angle':"0",'battery':"0", 'interval':"0",'RSSI':"0" }

#"name":"iSpindel001",
#"ID":14421487,
#"token":"fermentrack",
#"angle":57.54898,
#"temperature":24.1875,
#"temp_units":"C",
#"battery":4.103232,
#"gravity":16.9741,
#"interval":300,
#"RSSI":-68}

        # TODO - Add beer name to what is pushed

        latest_log_point = self.gravity_sensor_to_push.retrieve_latest_point()

        if latest_log_point is None:  # If there isn't an available log point, return nothing
            return {}

        # For now, if we can't get a latest log point, let's default to just not sending anything.
        if latest_log_point.gravity != 0.0:
            to_send['gravity'] = float(latest_log_point.gravity)
#           to_send['gravity_unit'] = "G"
        else:
            return {}  # Also return nothing if there isn't an available gravity

        # For now all gravity sensors have temp info, but just in case
        if latest_log_point.temp is not None:
            to_send['temperature'] = float(latest_log_point.temp)
            to_send['temp_units'] = latest_log_point.temp_format

        # TODO - Add linked BrewPi temps if we have them

        string_to_send = json.dumps(to_send)

        # We've got the data (in a json'ed string) - lets send it
        return string_to_send

    def send_data(self):
        # self.data_to_push() returns a JSON-encoded string which we will push directly out
        json_data = self.data_to_push()

        if len(json_data) <= 2:
            # There was no data to push - do nothing.
            return False

        headers = {'Content-Type': 'application/json'}

        r = requests.post(self.logging_url, data=json_data, headers=headers)
        return True  # TODO - Check if the post actually succeeded & react accordingly
