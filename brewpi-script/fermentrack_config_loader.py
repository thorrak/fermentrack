# This is an implementation of brewpiScriptConfig for Fermentrack. This manages loading BrewPiDevices from Fermentrack
# and populating their configuration data into a BrewPiScriptConfig object that can then be passed to BrewPi-Script

import os
import sys
from pathlib import Path
from typing import List

from django.core.exceptions import ObjectDoesNotExist

# Load up the Django specific stuff
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# This is so Django knows where to find stuff.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fermentrack_django.settings")
sys.path.append(BASE_DIR)
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
import app.models

from scriptlibs.brewpiScriptConfig import BrewPiScriptConfig


class FermentrackBrewPiScriptConfig(BrewPiScriptConfig):

    def __init__(self, brewpi_device_id):
        super().__init__()
        self.brewpi_device_id = brewpi_device_id
        self.brewpi_device = None
        self.uuid = None

    def load_from_fermentrack(self, false_on_connection_changes=False) -> bool:
        try:
            brewpi_device = app.models.BrewPiDevice.objects.get(id=self.brewpi_device_id)
        except ObjectDoesNotExist:
            return False  # cannot load the object from the database (deleted?)
        except RuntimeError:
            return False

        if self.uuid is None:
            self.uuid = brewpi_device.uuid
        else:
            if brewpi_device != self.uuid:
                # Something went really, really wrong.
                return False

        self.brewpi_device = brewpi_device

        self.status = brewpi_device.status
        self.logging_status = brewpi_device.logging_status
        self.temp_format = brewpi_device.temp_format
        self.active_beer_name = ""  # TODO - fix this
        self.data_point_log_interval = brewpi_device.data_point_log_interval

        # Interface to Script Connection Options
        if false_on_connection_changes:
            # The only thing that really should cause the script to restart is if there are configuration changes that
            # would interrupt the connection somehow.
            if self.use_inet_socket != brewpi_device.useInetSocket or self.socket_name != brewpi_device.socket_name \
                    or self.socket_host != brewpi_device.socketHost or self.socket_port != brewpi_device.socketPort:
                return False

        self.use_inet_socket = brewpi_device.useInetSocket
        self.socket_host = brewpi_device.socketHost
        self.socket_port = brewpi_device.socketPort
        self.socket_name = brewpi_device.socket_name

        # Script to Controller Connection Options
        self.connection_type = brewpi_device.connection_type
        self.prefer_connecting_via_udev = brewpi_device.prefer_connecting_via_udev

        # Serial Port Configuration Options
        self.serial_port = brewpi_device.serial_port
        self.serial_alt_port = brewpi_device.serial_alt_port
        self.udev_serial_number = brewpi_device.udev_serial_number

        # WiFi Configuration Options
        self.wifi_host = brewpi_device.wifi_host
        self.wifi_host_ip = brewpi_device.wifi_host_ip
        self.wifi_port = brewpi_device.wifi_port

        # Log File Path Configuration
        log_path = Path(__file__).parents[1] / "log"
        self.stderr_path = f'{log_path}/dev-{brewpi_device.id}-stderr.log'  # If left as an empty string, will log to stderr
        self.stdout_path = f'{log_path}/dev-{brewpi_device.id}-stdout.log'  # If left as an empty string, will log to stdout

    def get_profile_temp(self) -> float or None:
        # try:
        #     brewpi_device = app.models.BrewPiDevice.objects.get(id=self.brewpi_device_id)
        # except ObjectDoesNotExist:
        #     return None  # cannot load the object from the database (deleted?)
        return self.brewpi_device.get_profile_temp()

    def is_past_end_of_profile(self) -> bool:
        try:
            is_past_end = self.brewpi_device.is_past_end_of_profile()
        except StopIteration:
            is_past_end = False
        except RuntimeError:
            is_past_end = False
        return is_past_end

    def reset_profile(self):
        try:
            brewpi_device = app.models.BrewPiDevice.objects.get(id=self.brewpi_device_id)
        except ObjectDoesNotExist:
            return  # cannot load the object from the database (deleted?)
        return brewpi_device.reset_profile()

    def refresh(self) -> bool:
        return self.load_from_fermentrack(True)

    def save_host_ip(self, ip_to_save):
        # try:
        #     brewpi_device = app.models.BrewPiDevice.objects.get(id=self.brewpi_device_id)
        # except ObjectDoesNotExist:
        #     return  # cannot load the object from the database (deleted?)

        self.wifi_host_ip = ip_to_save
        # brewpi_device.wifi_host_ip = ip_to_save
        # brewpi_device.save()
        self.brewpi_device.wifi_host_ip = ip_to_save
        self.brewpi_device.save()

    def save_serial_port(self, serial_port_to_save):
        try:
            brewpi_device = app.models.BrewPiDevice.objects.get(id=self.brewpi_device_id)
        except ObjectDoesNotExist:
            return  # cannot load the object from the database (deleted?)

        brewpi_device.serial_port = serial_port_to_save
        self.serial_port = serial_port_to_save
        brewpi_device.save()

    def save_udev_serial_number(self, udev_serial_number):
        try:
            brewpi_device = app.models.BrewPiDevice.objects.get(id=self.brewpi_device_id)
        except ObjectDoesNotExist:
            return  # cannot load the object from the database (deleted?)

        brewpi_device.udev_serial_number = udev_serial_number
        self.udev_serial_number = udev_serial_number
        brewpi_device.save()

    def save_beer_log_point(self, beer_row):
        """
        Saves a row of data to the database (mapping the data row we are passed to Django's BeerLogPoint model)
        :param beer_row:
        :return:
        """
        try:
            brewpi_device = app.models.BrewPiDevice.objects.get(id=self.brewpi_device_id)
        except ObjectDoesNotExist:
            return  # cannot load the object from the database (deleted?)

        new_log_point = app.models.BeerLogPoint()

        new_log_point.beer_temp = beer_row['BeerTemp']
        new_log_point.beer_set = beer_row['BeerSet']
        new_log_point.beer_ann = beer_row['BeerAnn']

        new_log_point.fridge_temp = beer_row['FridgeTemp']
        new_log_point.fridge_set = beer_row['FridgeSet']
        new_log_point.fridge_ann = beer_row['FridgeAnn']

        new_log_point.room_temp = beer_row['RoomTemp']
        new_log_point.state = beer_row['State']

        new_log_point.temp_format = brewpi_device.temp_format
        new_log_point.associated_beer = brewpi_device.active_beer

        try:
            new_log_point.enrich_gravity_data()  # If gravity sensing is on, this will capture & populate everything
        except RuntimeError:
            # This gets tripped when there is an issue with enrich_gravity_data where the associated gravity sensor no
            # longer exists. This shouldn't happen, but can if the user goes poking around. Don't log the point - just
            # return.
            return

        new_log_point.save()


def get_active_brewpi_devices() -> List[int]:
    active_devices = app.models.BrewPiDevice.objects.filter(status=app.models.BrewPiDevice.STATUS_ACTIVE
                                                            ).values_list('id', flat=True)
    return active_devices
