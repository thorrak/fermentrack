from __future__ import unicode_literals

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

import os.path
import requests
import logging

import fhash

from constance import config

try:
    from fermentrack_django import settings
except:
    from fermentrack_com import settings  # This file is a direct copy of what I'm using for fermentrack.com. Simplifying keeping things in sync.

import re


logger = logging.getLogger(__name__)

FERMENTRACK_COM_URL = "http://www.fermentrack.com"

class DeviceFamily(models.Model):
    class Meta:
        verbose_name = "Device Family"
        verbose_name_plural = "Device Families"

    FLASH_ARDUINO = "avrdude"
    FLASH_ESP8266 = "esptool"

    FLASH_CHOICES=(
        (FLASH_ARDUINO, "Avrdude (Arduino)"),
        (FLASH_ESP8266, "Esptool (ESP8266)")
    )

    DETECT_ARDUINO = "arduino"
    DETECT_ESP8266 = "esp8266"
    DETECT_PARTICLE = "particle"

    DETECT_CHOICES = (
        (DETECT_ARDUINO, "Arduino"),
        (DETECT_ESP8266, "ESP8266"),
        (DETECT_PARTICLE, "Particle (Spark/Core)"),
    )

    name = models.CharField(max_length=30, blank=False, null=False, help_text="The name of the device family")
    flash_method = models.CharField(max_length=30, choices=FLASH_CHOICES, default=FLASH_ARDUINO)
    detection_family = models.CharField(max_length=30, choices=DETECT_CHOICES, default=DETECT_ARDUINO)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name

    @staticmethod
    def load_from_website():
        try:
            url = FERMENTRACK_COM_URL + "/api/firmware_family_list/"
            response = requests.get(url)
            data = response.json()
        except:
            return False

        if len(data) > 0:
            # If we got data, clear out the cache of DeviceFamilies
            DeviceFamily.objects.all().delete()
            # Then loop through the data we received and recreate it again
            for row in data:
                newDevice = DeviceFamily(name=row['name'], flash_method=row['flash_method'], id=row['id'],
                                         detection_family=row['detection_family'])
                newDevice.save()

            return True  # DeviceFamily table is updated
        return False  # We didn't get data back from Fermentrack.com, or there was an error

    def file_suffix(self):
        # file_suffix is used to determine the local filename for the firmware file

        if self.flash_method == self.FLASH_ARDUINO:
            return ".hex"
        elif self.flash_method == self.FLASH_ESP8266:
            return ".bin"
        else:
            return None


class Firmware(models.Model):
    class Meta:
        verbose_name = "Firmware"
        verbose_name_plural = "Firmware"  # I don't care if this is ambiguous, it bothers me.

    WEIGHT_CHOICES=(
        (1, "1 (Highest)"),
        (2, "2"),
        (3, "3"),
        (4, "4"),
        (5, "5"),
        (6, "6"),
        (7, "7"),
        (8, "8"),
        (9, "9  (Lowest)"),
    )

    name = models.CharField(max_length=128, blank=False, null=False, help_text="The name of the firmware")
    family = models.ForeignKey('DeviceFamily')

    version = models.CharField(max_length=20, default="0.0", help_text="The major version number")
    revision = models.CharField(max_length=20, default="0.0", help_text="The minor revision number")
    variant = models.CharField(max_length=80, default="", blank=True, help_text="The firmware 'variant' (if applicable)")

    is_fermentrack_supported = models.BooleanField(default=False,
                                                   help_text="Is this firmware officially supported by Fermentrack?")

    in_error = models.BooleanField(default=False, help_text="Is there an error with this firmware that should "
                                                            "prevent it from being downloaded?")

    description = models.TextField(default="", blank=True, null=False, help_text="The description of the firmware")
    variant_description = models.TextField(default="", blank=True, null=False, help_text="The description of the variant")

    download_url = models.CharField(max_length=255, default="", blank=True, null=False,
                                    help_text="The URL at which the firmware can be downloaded")
    project_url = models.CharField(max_length=255, default="", blank=True, null=False,
                                   help_text="The URL for the project associated with the firmware")
    documentation_url = models.CharField(max_length=255, default="", blank=True, null=False,
                                         help_text="The URL for documentation/help on the firmware (if any)")

    weight = models.IntegerField(default=5, help_text="Weight for sorting (Lower weights rise to the top)", choices=WEIGHT_CHOICES)

    checksum = models.CharField(max_length=64, help_text="SHA256 checksum of the file (for checking validity)",
                                default="", blank=True)

    def __str__(self):
        return self.name + " - " + self.version + " - " + self.revision + " - " + self.variant

    def __unicode__(self):
        return self.__str__()

    @staticmethod
    def load_from_website():
        try:
            url = FERMENTRACK_COM_URL + "/api/firmware_list/all/"
            response = requests.get(url)
            data = response.json()
        except:
            return False

        if len(data) > 0:
            # If we got data, clear out the cache of Firmware
            Firmware.objects.all().delete()
            # Then loop through the data we received and recreate it again
            for row in data:
                newFirmware = Firmware(
                    name=row['name'], version=row['version'], revision=row['revision'], family_id=row['family_id'],
                    variant=row['variant'], is_fermentrack_supported=row['is_fermentrack_supported'],
                    in_error=row['in_error'], description=row['description'],
                    variant_description=row['variant_description'], download_url=row['download_url'],
                    project_url=row['project_url'], documentation_url=row['documentation_url'], weight=row['weight'],
                    checksum=row['checksum'],
                )
                newFirmware.save()

            return True  # Firmware table is updated
        return False  # We didn't get data back from Fermentrack.com, or there was an error


    def local_filename(self):
        def stripslashes(string):
            return string.replace('\\', '').replace('/', '')
        fname_base =  stripslashes(self.family.name) + " - " + stripslashes(self.name) + " - "
        fname_base += "v" + stripslashes(self.version) + "r" + stripslashes(self.revision)
        if len(self.variant) > 0:
            fname_base += " -- " + stripslashes(self.variant)
        fname_base += self.family.file_suffix()

        return fname_base

    def local_filepath(self):
        return os.path.join(settings.BASE_DIR, "firmware_flash", "firmware")

    def download_to_file(self, check_checksum=True, force_download=False):
        full_path = os.path.join(self.local_filepath(), self.local_filename())

        if os.path.isfile(full_path):
            if force_download:  # If we're just going to force the download anyways, just kill the file
                os.remove(full_path)
            elif self.checksum == fhash.hash_of_file(full_path):  # If the file already exists check the checksum
                # The file is valid - return the path
                return full_path
            else:
                # The checksum check failed - Kill the file
                os.remove(full_path)

        # So either we don't have a downloaded copy (or it's invalid). Let's download a new one.
        r = requests.get(self.download_url, stream=True)

        with open(full_path, str("wb")) as f:
            for chunk in r.iter_content():
                f.write(chunk)

        # Now, let's check that the file is valid (but only if check_checksum is true)
        if check_checksum:
            if os.path.isfile(full_path):
                # If the file already exists check the checksum (and delete if it fails)
                if self.checksum != fhash.hash_of_file(full_path):
                    os.remove(full_path)
                    return None
            else:
                return None
        # The file is valid (or we aren't checking checksums). Return the path.
        return full_path


class Board(models.Model):
    class Meta:
        verbose_name = "Board"
        verbose_name_plural = "Boards"

    WEIGHT_CHOICES=(
        (1, "1 (Highest)"),
        (2, "2"),
        (3, "3"),
        (4, "4"),
        (5, "5"),
        (6, "6"),
        (7, "7"),
        (8, "8"),
        (9, "9  (Lowest)"),
    )

    name = models.CharField(max_length=128, blank=False, null=False, help_text="The name of the board")

    family = models.ForeignKey('DeviceFamily')

    description = models.TextField(default="", blank=True, null=False, help_text="The description of the board")

    weight = models.IntegerField(default=5, help_text="Weight for sorting (Lower weights rise to the top)",
                                 choices=WEIGHT_CHOICES)

    flash_options_json = models.TextField(default="", blank=True, null=False,
                                          help_text="A JSON list containing options to pass to subprocess")

    @staticmethod
    def load_from_website():
        try:
            url = FERMENTRACK_COM_URL + "/api/board_list/all/"
            response = requests.get(url)
            data = response.json()
        except:
            return False

        if len(data) > 0:
            # If we got data, clear out the cache of Firmware
            Board.objects.all().delete()
            # Then loop through the data we received and recreate it again
            for row in data:
                newBoard = Board(
                    name=row['name'], family_id=row['family_id'], description=row['description'], weight=row['weight'],
                    flash_options_json=row['flash_options_json'], id=row['id'],
                )
                newBoard.save()

            return True  # Board table is updated
        return False  # We didn't get data back from Fermentrack.com, or there was an error

