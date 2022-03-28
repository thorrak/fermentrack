from __future__ import unicode_literals

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

import os.path
import requests
import logging

from . import fhash

from constance import config

try:
    from fermentrack_django import settings
except:
    from fermentrack_com import \
        settings  # This file is a direct copy of what I'm using for fermentrack.com. Simplifying keeping things in sync.

logger = logging.getLogger(__name__)

FERMENTRACK_COM_URL = "https://www.fermentrack.com"
MODEL_VERSION = 3


def check_model_version():
    try:
        url = FERMENTRACK_COM_URL + "/api/model_version/"
        response = requests.get(url)
        data = response.json()
    except:
        return False

    return data


def get_model_version():
    return MODEL_VERSION


class DeviceFamily(models.Model):
    class Meta:
        verbose_name = "Device Family"
        verbose_name_plural = "Device Families"

    FLASH_ARDUINO = "avrdude"
    FLASH_ESP = "esptool"

    FLASH_CHOICES = (
        (FLASH_ARDUINO, "Avrdude (Arduino)"),
        (FLASH_ESP, "Esptool (ESP8266)")
    )

    DETECT_ARDUINO = "arduino"
    DETECT_ESP8266 = "esp8266"
    DETECT_PARTICLE = "particle"
    DETECT_ESP32 = "esp32"

    DETECT_CHOICES = (
        (DETECT_ARDUINO, "Arduino"),
        (DETECT_ESP8266, "ESP8266"),
        (DETECT_PARTICLE, "Particle (Spark/Core)"),
        (DETECT_ESP32, "ESP32"),
    )

    name = models.CharField(max_length=30, blank=False, null=False, help_text="The name of the device family")
    flash_method = models.CharField(max_length=30, choices=FLASH_CHOICES, default=FLASH_ARDUINO)
    detection_family = models.CharField(max_length=30, choices=DETECT_CHOICES, default=DETECT_ARDUINO)

    def __str__(self):
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
                try:
                    # This gets wrapped in a try/except as I don't want this failing if the local copy of Fermentrack
                    # is slightly behind what is available at Fermentrack.com (eg - if there are new device families)
                    newDevice = DeviceFamily(name=row['name'], flash_method=row['flash_method'], id=row['id'],
                                             detection_family=row['detection_family'])
                    newDevice.save()
                except:
                    pass

            return True  # DeviceFamily table is updated
        return False  # We didn't get data back from Fermentrack.com, or there was an error

    def file_suffix(self):
        # file_suffix is used to determine the local filename for the firmware file

        if self.flash_method == self.FLASH_ARDUINO:
            return ".hex"
        elif self.flash_method == self.FLASH_ESP:
            return ".bin"
        else:
            return None


class Firmware(models.Model):
    class Meta:
        verbose_name = "Firmware"
        verbose_name_plural = "Firmware"  # I don't care if this is ambiguous, it bothers me.

    WEIGHT_CHOICES = (
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
    family = models.ForeignKey('DeviceFamily', on_delete=models.CASCADE)

    version = models.CharField(max_length=20, default="0.0", help_text="The major version number")
    revision = models.CharField(max_length=20, default="", help_text="The minor revision number", blank=True)
    variant = models.CharField(max_length=80, default="", blank=True,
                               help_text="The firmware 'variant' (if applicable)")

    is_fermentrack_supported = models.BooleanField(default=False,
                                                   help_text="Is this firmware officially supported by Fermentrack?")

    in_error = models.BooleanField(default=False, help_text="Is there an error with this firmware that should "
                                                            "prevent it from being downloaded?")

    description = models.TextField(default="", blank=True, null=False, help_text="The description of the firmware")
    variant_description = models.TextField(default="", blank=True, null=False,
                                           help_text="The description of the variant")
    post_install_instructions = models.TextField(default="", blank=True, null=False,
                                                 help_text="Instructions to be displayed to the user after installation")

    download_url = models.CharField(max_length=255, default="", blank=True, null=False,
                                    help_text="The URL at which the firmware can be downloaded")
    download_url_partitions = models.CharField(max_length=255, default="", blank=True, null=False,
                                               help_text="The URL at which the partitions binary can be downloaded (ESP32 only, optional)")
    download_url_spiffs = models.CharField(max_length=255, default="", blank=True, null=False,
                                           help_text="The URL at which the SPIFFS binary can be downloaded (optional)")

    download_url_bootloader = models.CharField(max_length=255, default="", blank=True, null=False,
                                               help_text="The URL at which the bootloader binary can be downloaded (ESP32 only, optional)")

    download_url_otadata = models.CharField(max_length=255, default="", blank=True, null=False,
                                            help_text="The URL at which the OTA Dta binary can be downloaded (ESP32 only, optional)")

    spiffs_address = models.CharField(max_length=12, default="", blank=True, null=False,
                                           help_text="The flash address the SPIFFS data should be flashed to")

    otadata_address = models.CharField(max_length=12, default="", blank=True, null=False,
                                           help_text="The flash address the SPIFFS data should be flashed to (ESP32 only)")



    weight = models.IntegerField(default=5, help_text="Weight for sorting (Lower weights rise to the top)",
                                 choices=WEIGHT_CHOICES)

    checksum = models.CharField(max_length=64, help_text="SHA256 checksum of the file (for checking validity)",
                                default="", blank=True)
    checksum_partitions = models.CharField(max_length=64, help_text="SHA256 checksum of the partitions file (for checking validity)",
                                           default="", blank=True)
    checksum_spiffs = models.CharField(max_length=64, help_text="SHA256 checksum of the SPIFFS file (for checking validity)",
                                       default="", blank=True)
    checksum_bootloader = models.CharField(max_length=64, help_text="SHA256 checksum of the bootloader file (for checking validity)",
                                           default="", blank=True)
    checksum_otadata = models.CharField(max_length=64, help_text="SHA256 checksum of the otadata file (for checking validity)",
                                       default="", blank=True)


    project = models.ForeignKey('Project', on_delete=models.SET_NULL, default=None, null=True)

    def __str__(self):
        return self.name + " - " + self.version + " - " + self.revision + " - " + self.variant

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
                    variant_description=row['variant_description'], download_url=row['download_url'],weight=row['weight'],
                    download_url_partitions=row['download_url_partitions'],
                    download_url_spiffs=row['download_url_spiffs'], checksum=row['checksum'],
                    checksum_partitions=row['checksum_partitions'], checksum_spiffs=row['checksum_spiffs'],
                    spiffs_address=row['spiffs_address'], project_id=row['project_id'],
                    download_url_bootloader=row['download_url_bootloader'],
                    checksum_bootloader=row['checksum_bootloader'],
                    download_url_otadata=row['download_url_otadata'],
                    otadata_address=row['otadata_address'], checksum_otadata=row['checksum_otadata'],
                )
                newFirmware.save()

            return True  # Firmware table is updated
        return False  # We didn't get data back from Fermentrack.com, or there was an error

    def local_filename(self, bintype):
        def stripslashes(string):
            return string.replace('\\', '').replace('/', '')

        fname_base = stripslashes(self.family.name) + " - " + stripslashes(self.name) + " - "
        fname_base += "v" + stripslashes(self.version) + "r" + stripslashes(self.revision)
        if len(self.variant) > 0:
            fname_base += " -- " + stripslashes(self.variant)

        fname_base += " - " + stripslashes(bintype)  # For SPIFFS, Partition, etc.

        fname_base += self.family.file_suffix()

        return fname_base

    @classmethod
    def local_filepath(cls):
        return settings.ROOT_DIR / "firmware_flash" / "firmware"

    def full_filepath(self, bintype):
        return self.local_filepath() / self.local_filename(bintype)

    @classmethod
    def download_file(cls, full_path, url, checksum, check_checksum, force_download):
        if os.path.isfile(full_path):
            if force_download:  # If we're just going to force the download anyways, just kill the file
                os.remove(full_path)
            elif checksum == fhash.hash_of_file(full_path):  # If the file already exists check the checksum
                # The file is valid - return the path
                return True
            else:
                # The checksum check failed - Kill the file
                os.remove(full_path)

        if len(url) < 12:  # If we don't have a URL, we can't download anything
            return False

        # So either we don't have a downloaded copy (or it's invalid). Let's download a new one.
        r = requests.get(url, stream=True)

        with open(full_path, str("wb")) as f:
            for chunk in r.iter_content():
                f.write(chunk)

        # Now, let's check that the file is valid (but only if check_checksum is true)
        if check_checksum:
            if os.path.isfile(full_path):
                # If the file already exists check the checksum (and delete if it fails)
                if checksum != fhash.hash_of_file(full_path):
                    os.remove(full_path)
                    return False
            else:
                return False
        # The file is valid (or we aren't checking checksums). Return the path.
        return True

    def download_to_file(self, check_checksum=True, force_download=False):
        # If this is a multi-part firmware (ESP32, with partitions or SPIFFS) then download the additional parts.
        if len(self.download_url_partitions) > 12:
            if not self.download_file(self.full_filepath("partitions"), self.download_url_partitions,
                                      self.checksum_partitions, check_checksum, force_download):
                return False

        if len(self.download_url_spiffs) > 12 and len(self.spiffs_address) > 2:
            if not self.download_file(self.full_filepath("spiffs"), self.download_url_spiffs,
                                      self.checksum_spiffs, check_checksum, force_download):
                return False

        if len(self.download_url_bootloader) > 12:
            if not self.download_file(self.full_filepath("bootloader"), self.download_url_bootloader,
                                      self.checksum_bootloader, check_checksum, force_download):
                return False

        if len(self.download_url_otadata) > 12 and len(self.otadata_address) > 2:
            if not self.download_file(self.full_filepath("otadata"), self.download_url_otadata,
                                      self.checksum_otadata, check_checksum, force_download):
                return False

        # Always download the main firmware
        return self.download_file(self.full_filepath("firmware"), self.download_url, self.checksum, check_checksum, force_download)


class Board(models.Model):
    class Meta:
        verbose_name = "Board"
        verbose_name_plural = "Boards"

    WEIGHT_CHOICES = (
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

    family = models.ForeignKey('DeviceFamily', on_delete=models.CASCADE)

    description = models.TextField(default="", blank=True, null=False, help_text="The description of the board")

    weight = models.IntegerField(default=5, help_text="Weight for sorting (Lower weights rise to the top)",
                                 choices=WEIGHT_CHOICES)

    flash_options_json = models.TextField(default="", blank=True, null=False,
                                          help_text="A JSON list containing options to pass to subprocess")

    def __str__(self):
        return self.name + " - " + str(self.family)

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
                try:
                    # This gets wrapped in a try/except as I don't want this failing if the local copy of Fermentrack
                    # is slightly behind what is available at Fermentrack.com (eg - if there are new device families)
                    newBoard = Board(
                        name=row['name'], family_id=row['family_id'], description=row['description'], weight=row['weight'],
                        flash_options_json=row['flash_options_json'], id=row['id'],
                    )
                    newBoard.save()
                except:
                    pass

            return True  # Board table is updated
        return False  # We didn't get data back from Fermentrack.com, or there was an error


class FlashRequest(models.Model):
    STATUS_QUEUED = 'queued'
    STATUS_RUNNING = 'running'
    STATUS_FINISHED = 'finished'
    STATUS_FAILED = 'failed'

    STATUS_CHOICES = (
        (STATUS_QUEUED, 'Queued'),
        (STATUS_RUNNING, 'Running'),
        (STATUS_FINISHED, 'Finished'),
        (STATUS_FAILED, 'Failed'),
    )

    # huey_task_id = models.CharField(max_length=64, help_text="Task ID used within Huey for tracking status")
    status = models.CharField(max_length=32, default=STATUS_QUEUED)
    firmware_to_flash = models.ForeignKey('Firmware', on_delete=models.CASCADE, help_text="Firmware to flash")
    board_type = models.ForeignKey('Board', on_delete=models.CASCADE, help_text="Board type being flashed")
    serial_port = models.CharField(max_length=255, help_text="Path to the serial device used with the flash tool")
    result_text = models.CharField(max_length=255, default=None, blank=True, null=True,
                                   help_text="String explaining the result status")
    flash_output = models.TextField(null=True, blank=True, default=None, help_text="Output from the flash tool")
    created = models.DateTimeField(help_text="The date this flash request was created", auto_now_add=True)

    def fail(self, result_text, flash_output=""):
        """ FlashRequest.fail is just a fast way to set the status & result text and save the object """
        self.result_text = result_text
        self.flash_output = flash_output
        self.status = self.STATUS_FAILED
        self.save()
        return True

    def succeed(self, result_text, flash_output=""):
        """ FlashRequest.succeed is just a fast way to set the status & result text and save the object """
        self.result_text = result_text
        self.flash_output = flash_output
        self.status = self.STATUS_FINISHED
        self.save()
        return True


class Project(models.Model):
    class Meta:
        verbose_name = "Project"
        verbose_name_plural = "Projects"

    WEIGHT_CHOICES = (
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

    name = models.CharField(max_length=128, blank=False, null=False,
                            help_text="The name of the project the firmware is associated with")
    description = models.TextField(default="", blank=True, null=False, help_text="The description of the project")
    project_url = models.CharField(max_length=255, default="", blank=True, null=False,
                                   help_text="The URL for the project associated with the firmware")
    documentation_url = models.CharField(max_length=255, default="", blank=True, null=False,
                                         help_text="The URL for documentation/help on the firmware (if any)")
    support_url = models.CharField(max_length=255, default="", blank=True, null=False,
                                         help_text="The URL for support (if any, generally a forum thread)")
    weight = models.IntegerField(default=5, help_text="Weight for sorting (Lower weights rise to the top)",
                                 choices=WEIGHT_CHOICES)
    show_in_standalone_flasher = models.BooleanField(default=False, help_text="Should this show standalone flash app?")

    def __str__(self):
        return self.name

    @staticmethod
    def load_from_website():
        try:
            url = FERMENTRACK_COM_URL + "/api/project_list/all/"
            response = requests.get(url)
            data = response.json()
        except:
            return False

        if len(data) > 0:
            # If we got data, clear out the cache of Firmware
            Project.objects.all().delete()
            # Then loop through the data we received and recreate it again
            for row in data:
                newProject = Project(
                    name=row['name'], project_url=row['project_url'], documentation_url=row['documentation_url'], weight=row['weight'],
                    support_url=row['support_url'], id=row['id'], description=row['description']
                )
                newProject.save()

            return True  # Project table is updated
        return False  # We didn't get data back from Fermentrack.com, or there was an error


