# Create your tasks here
from __future__ import absolute_import, unicode_literals
from huey.contrib.djhuey import periodic_task, task, db_periodic_task, db_task
from . import models
from app.models import BrewPiDevice

import os, subprocess, datetime, pytz, time
import json



@db_task()
def flash_firmware(flash_request_id):
    flash_request = models.FlashRequest.objects.get(id=flash_request_id)

    # Set the status to "running" to provide additional feedback if something goes wrong
    flash_request.status = models.FlashRequest.STATUS_RUNNING
    flash_request.save()

    if not flash_request.firmware_to_flash.download_to_file():
        flash_request.fail("Unable to download firmware file(s)!")
        return None

    firmware_path = str(flash_request.firmware_to_flash.full_filepath("firmware"))

    # Ok, we now have the firmware file. Let's do something with it
    if flash_request.firmware_to_flash.family.flash_method == models.DeviceFamily.FLASH_ESP:
        # We're using an ESP8266/ESP32, which means esptool.
        flash_cmd = ["esptool.py"]
    elif flash_request.firmware_to_flash.family.flash_method == models.DeviceFamily.FLASH_ARDUINO:
        flash_cmd = ["avrdude"]
    else:
        flash_request.fail("Device family {} is unsupported in this version of Fermentrack!".format(
            flash_request.firmware_to_flash.family))
        return None

    flash_args = json.loads(flash_request.board_type.flash_options_json)

    for arg in flash_args:
        flash_cmd.append(str(arg).replace("{serial_port}", flash_request.serial_port).replace("{firmware_path}",
                                                                                              firmware_path))

    # For ESP32 devices only, we need to check if we want to flash partitions or a bootloader. I may need to add
    # ESP8266 support for flashing a bootloader later - if I do, the code for adding the bootloader command to the
    # below needs to be moved to the SPIFFS/
    if flash_request.board_type.family.detection_family == models.DeviceFamily.DETECT_ESP32:
        # First, check if we have a partitions file to flash
        if len(flash_request.firmware_to_flash.download_url_partitions) > 0 and len(flash_request.firmware_to_flash.checksum_partitions) > 0:
            # We need to flash partitions. Partitions are (currently) always at 0x8000
            flash_cmd.append("0x8000")
            flash_cmd.append(str(flash_request.firmware_to_flash.full_filepath("partitions")))

        if len(flash_request.firmware_to_flash.download_url_bootloader) > 0 and \
                 len(flash_request.firmware_to_flash.checksum_bootloader) > 0:
            # The ESP32 bootloader is always flashed to 0x1000
            flash_cmd.append("0x1000")
            flash_cmd.append(str(flash_request.firmware_to_flash.full_filepath("bootloader")))



    # SPIFFS (and maybe otadata?) flashing can be done on either the ESP8266 or the ESP32
    if flash_request.firmware_to_flash.family.flash_method == models.DeviceFamily.FLASH_ESP:
        # Check for SPIFFS first
        if len(flash_request.firmware_to_flash.download_url_spiffs) > 0 and \
                 len(flash_request.firmware_to_flash.checksum_spiffs) > 0 and \
                 len(flash_request.firmware_to_flash.spiffs_address) > 2:
            # We need to flash SPIFFS. The location is dependent on the partition scheme, so we need to use the address
            flash_cmd.append(flash_request.firmware_to_flash.spiffs_address)
            flash_cmd.append(str(flash_request.firmware_to_flash.full_filepath("spiffs")))
        # Then check for otadata
        if len(flash_request.firmware_to_flash.download_url_otadata) > 0 and \
                 len(flash_request.firmware_to_flash.checksum_otadata) > 0 and \
                 len(flash_request.firmware_to_flash.otadata_address) > 2:
            # We need to flash otadata. The location is dependent on the partition scheme, so we need to use the address
            flash_cmd.append(flash_request.firmware_to_flash.otadata_address)
            flash_cmd.append(str(flash_request.firmware_to_flash.full_filepath("otadata")))


    # TODO - Explicitly need to disable any device on that port
    # If we are running as part of a fermentrack installation (which presumably, we are) we need to disable
    # any device currently running on the serial port we're flashing.

    devices_to_disable = BrewPiDevice.objects.filter(status=BrewPiDevice.STATUS_ACTIVE)

    for this_device in devices_to_disable:
        this_device.status = BrewPiDevice.STATUS_UPDATING
        this_device.save()
        time.sleep(10)  # Give the process manager time to refresh & disable the script

    # And now, let's call the actual flasher
    try:
        output_text = "Flash Command: " + " ".join(flash_cmd) + "\r\n\r\n"
        output_text += subprocess.check_output(flash_cmd).decode(encoding="cp437")
    except subprocess.CalledProcessError as e:
        flash_request.fail("Flash process returned code {}".format(e.returncode), e.output)
        return None

    # Last, reenable all the devices we disabled earlier
    devices_to_disable = BrewPiDevice.objects.filter(status=BrewPiDevice.STATUS_UPDATING)
    for this_device in devices_to_disable:
        this_device.status = BrewPiDevice.STATUS_ACTIVE
        this_device.save()
        # We'll let the process manager restart the process on the next cycle

    flash_request.succeed("Flash completed successfully", output_text)

    # TODO - See if we can return something here
    return None
