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

    firmware_path = flash_request.firmware_to_flash.download_to_file()
    if firmware_path is None:
        flash_request.fail("Unable to download firmware file!")
        return None

    # Ok, we now have the firmware file. Let's do something with it
    if flash_request.firmware_to_flash.family.flash_method == models.DeviceFamily.FLASH_ESP8266:
        # We're using an ESP8266, which means esptool.
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

    # TODO - Explicitly need to disable any device on that port
    # If we are running as part of a fermentrack installation (which presumably, we are) we need to disable
    # any device currently running on the serial port we're flashing.

    devices_to_disable = BrewPiDevice.objects.filter(status=BrewPiDevice.STATUS_ACTIVE)

    for this_device in devices_to_disable:
        this_device.status = BrewPiDevice.STATUS_UPDATING
        this_device.save()
        try:
            this_device.stop_process()
        except:
            # Depending on how quickly circus checks, this may cause a race condition as the process gets
            # stopped twice
            pass

    # And now, let's call the actual flasher
    try:
        output_text = subprocess.check_output(flash_cmd)
    except (subprocess.CalledProcessError) as e:
        flash_request.fail("Flash process returned code {}".format(e.returncode), e.output)
        return None

    # Last, reenable all the devices we disabled earlier
    devices_to_disable = BrewPiDevice.objects.filter(status=BrewPiDevice.STATUS_UPDATING)
    for this_device in devices_to_disable:
        this_device.status = BrewPiDevice.STATUS_ACTIVE
        this_device.save()
        # We'll let Circus restart the process on the next cycle
        # this_device.start_process()

    flash_request.succeed("Flash completed successfully", output_text)

    # TODO - See if we can return something here
    return None
