from django.shortcuts import render
from django.contrib import messages
from django.shortcuts import render_to_response, redirect
from django.contrib.auth import login
from django.contrib.auth.models import User
from constance import config
from django.contrib.auth.decorators import login_required

import forms

from app.models import BrewPiDevice
from firmware_flash.models import DeviceFamily, Firmware

import app.serial_integration as serial_integration

from app.decorators import site_is_configured  # Checks if user has completed constance configuration
import random

import os, subprocess

# Fermentrack integration
try:
    from app.models import BrewPiDevice
    FERMENTRACK_INTEGRATION = True
except:
    FERMENTRACK_INTEGRATION = False


def render_with_devices(request, template_name, context=None, content_type=None, status=None, using=None):
    all_devices = BrewPiDevice.objects.all()

    if context:  # Append to the context dict if it exists, otherwise create the context dict to add
        context['all_devices'] = all_devices
    else:
        context={'all_devices': all_devices}

    return render(request, template_name, context, content_type, status, using)





@login_required
@site_is_configured
def firmware_select_family(request):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.add_device'):
    #     messages.error(request, 'Your account is not permissioned to add devices. Please contact an admin')
    #     return redirect("/")

    # Test if avrdude is available. If not, the user will need to install it.
    try:
        rettext = subprocess.check_output(["dpkg", "-s", "avrdude"])
        install_check = rettext.find("installed")

        if install_check == -1:
            # The package status isn't installed
            # TODO - Provide link to instructions on how to resolve this error.
            messages.warning(request, "Warning - Package 'avrdude' not installed. Arduino installations will fail!")
    except:
        messages.error(request, "Error checking for installed 'avrdude' package - Arduino installations may fail!")


    if request.POST:
        form = forms.FirmwareFamilyForm(request.POST)
        if form.is_valid():
            return redirect('firmware_flash_serial_autodetect', flash_family_id=form.cleaned_data['device_family'])
        else:
            return render_with_devices(request, template_name='firmware_flash/select_family.html', context={'form': form})
    else:
        form = forms.FirmwareFamilyForm()
        return render_with_devices(request, template_name='firmware_flash/select_family.html', context={'form': form})



def refresh_firmware():
    # First, load the device family list
    families_loaded = DeviceFamily.load_from_website()

    if families_loaded:
        # And if that worked, load the firmware list
        firmware_loaded = Firmware.load_from_website()
    else:
        # If it didn't work, return False
        return False

    return firmware_loaded


@login_required
@site_is_configured
def firmware_refresh_list(request):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.add_device'):
    #     messages.error(request, 'Your account is not permissioned to add devices. Please contact an admin')
    #     return redirect("/")

    if refresh_firmware():
        messages.success(request, "Firmware list was successfully refreshed from Fermentrack.com")
    else:
        messages.error(request, "Firmware list was not able to be refreshed from Fermentrack.com")

    return redirect('firmware_flash_select_family')



# NOTE - This is a modified version of device_guided_serial_autodetect
@login_required
@site_is_configured
def firmware_flash_serial_autodetect(request, flash_family_id):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.add_device'):
    #     messages.error(request, 'Your account is not permissioned to add devices. Please contact an admin')
    #     return redirect("/")

    # device_guided_serial_autodetect contains all 4 steps in the Serial autodetection guided setup.

    try:
        flash_family = DeviceFamily.objects.get(id=flash_family_id)
    except:
        messages.error(request, "Invalid flash_family specified")
        return redirect('firmware_flash_select_family')

    if not request.POST:
        # If we haven't had something posted to us, provide the instructions page. (Step 1)
        return render_with_devices(request, template_name='firmware_flash/serial_autodetect_1.html',
                                   context={'flash_family_id': flash_family_id})

    else:
        # Something was posted - figure out what step we're on by looking at the "step" field
        if 'step' not in request.POST:
            # We received a form, but not the right form. Redirect to the start of the autodetection flow.
            return render_with_devices(request, template_name='firmware_flash/serial_autodetect_1.html',
                                       context={'flash_family_id': flash_family_id})
        elif request.POST['step'] == "2":
            # Step 2 - Cache the current devices & present the next set of instructions to the user
            current_devices = serial_integration.cache_current_devices()
            return render_with_devices(request, template_name='firmware_flash/serial_autodetect_2.html',
                                       context={'flash_family_id': flash_family_id, 'current_devices': current_devices})
        elif request.POST['step'] == "3":
            # Step 3 - Detect newly-connected devices & prompt the user to select the one that corresponds to the
            # device they want to configure.
            _, _, _, new_devices_enriched = serial_integration.compare_current_devices_against_cache(flash_family.detection_family)
            return render_with_devices(request, template_name='firmware_flash/serial_autodetect_3.html',
                                       context={'flash_family_id': flash_family_id, 'new_devices': new_devices_enriched})
        else:
            # The step number we received was invalid. Redirect to the start of the autodetection flow.
            return render_with_devices(request, template_name='setup/device_guided_serial_autodetect_1.html',
                                       context={'flash_family_id': flash_family_id})


@login_required
@site_is_configured
def firmware_flash_select_firmware(request, flash_family_id):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.add_device'):
    #     messages.error(request, 'Your account is not permissioned to add devices. Please contact an admin')
    #     return redirect("/")

    try:
        flash_family = DeviceFamily.objects.get(id=flash_family_id)
    except:
        messages.error(request, "Invalid flash_family specified")
        return redirect('firmware_flash_select_family')

    if not request.POST:
        # If we weren't passed anything in request.POST, kick the user back to the autodetect routine
        return render_with_devices(request, template_name='firmware_flash/serial_autodetect_1.html',
                                   context={'flash_family_id': flash_family_id})

    if 'serial_port' not in request.POST:
        # Same if we weren't explicitly passed request.POST['serial_port']
        messages.error(request, "Serial port wasn't provided to 'select_firmware'. Please restart serial autodetection & try again.")
        return render_with_devices(request, template_name='firmware_flash/serial_autodetect_1.html',
                                   context={'flash_family_id': flash_family_id})


    fermentrack_firmware = Firmware.objects.filter(is_fermentrack_supported=True, in_error=False, family=flash_family).order_by('weight')
    other_firmware = Firmware.objects.filter(is_fermentrack_supported=False, in_error=False, family=flash_family).order_by('weight')
    error_firmware = Firmware.objects.filter(in_error=True, family=flash_family).order_by('weight')

    return render_with_devices(request, template_name='firmware_flash/select_firmware.html',
                               context={'other_firmware': other_firmware, 'fermentrack_firmware': fermentrack_firmware,
                                        'flash_family': flash_family, 'error_firmware': error_firmware,
                                        'serial_port': request.POST['serial_port']})


@login_required
@site_is_configured
def firmware_flash_flash_firmware(request, flash_family_id):
    # TODO - Strip flash_family_id from being passed in, as we can pull it from the passed firmware_id
    try:
        flash_family = DeviceFamily.objects.get(id=flash_family_id)
    except:
        messages.error(request, "Invalid flash_family specified")
        return redirect('firmware_flash_select_family')

    if not request.POST:
        # If we weren't passed anything in request.POST, kick the user back to the autodetect routine
        return render_with_devices(request, template_name='firmware_flash/serial_autodetect_1.html',
                                   context={'flash_family_id': flash_family_id})

    if 'serial_port' not in request.POST:
        # Same if we weren't explicitly passed request.POST['serial_port']
        messages.error(request, "Serial port wasn't provided to 'select_firmware'. Please restart serial autodetection & try again.")
        return render_with_devices(request, template_name='firmware_flash/serial_autodetect_1.html',
                                   context={'flash_family_id': flash_family_id})

    if 'firmware_id' not in request.POST:
        messages.error(request, "Invalid firmware ID was specified! Please restart serial autodetection & try again.")
        return render_with_devices(request, template_name='firmware_flash/serial_autodetect_1.html',
                                   context={'flash_family_id': flash_family_id})

    try:
        firmware_to_flash = Firmware.objects.get(id=request.POST['firmware_id'])
    except:
        messages.error(request, "Invalid firmware ID was specified! Please restart serial autodetection & try again.")
        return render_with_devices(request, template_name='firmware_flash/serial_autodetect_1.html',
                                   context={'flash_family_id': flash_family_id})

    # Alright. Now we need to flash the firmware. First, download the selected firmware file
    device_flashed = False
    firmware_path = firmware_to_flash.download_to_file()
    if firmware_path is None:
        messages.error(request, "Unable to download firmware file!")
        flash_cmd = None
    else:
        # Ok, we now have the firmware file. Let's do something with it
        if firmware_to_flash.family.flash_method == DeviceFamily.FLASH_ESP8266:
            # We're using an ESP8266, which means esptool.
            flash_cmd = ["esptool.py", "--port", request.POST['serial_port'], "write_flash", "--flash_mode", "dio", "0x00000", firmware_path]
        else:
            flash_cmd = []

        # TODO - Explicitly need to disable any device on that port
        if FERMENTRACK_INTEGRATION:
            # If we are running as part of a fermentrack installation (which presumably, we are) we need to disable
            # any device currently running on the serial port we're flashing.

            devices_to_disable = BrewPiDevice.objects.filter(status=BrewPiDevice.STATUS_ACTIVE)

            for this_device in devices_to_disable:
                this_device.status = BrewPiDevice.STATUS_UPDATING
                this_device.save()
                this_device.stop_process()

        # And now, let's call the actual flasher
        retval = subprocess.call(flash_cmd)

        # Last, reenable all the devices we disabled earlier
        if FERMENTRACK_INTEGRATION:
            devices_to_disable = BrewPiDevice.objects.filter(status=BrewPiDevice.STATUS_UPDATING)
            for this_device in devices_to_disable:
                this_device.status = BrewPiDevice.STATUS_ACTIVE
                this_device.save()
                # We'll let Circus restart the process on the next cycle
                # this_device.start_process()

        if retval == 0:
            messages.success(request, "Firmware successfully flashed to device!")
            device_flashed = True
        else:
            messages.error(request, "Firmware didn't flash successfully. Please reattempt, or flash manually.")

    return render_with_devices(request, template_name='firmware_flash/flash_firmware.html',
                               context={'flash_family': flash_family, 'firmware': firmware_to_flash,
                                        'flash_cmd': flash_cmd, 'device_flashed': device_flashed})




# TODO - Delete this view!!
@login_required
@site_is_configured
def firmware_flash_test_select_firmware(request):
    try:
        flash_family = DeviceFamily.objects.get(name="ESP8266")
    except:
        messages.error(request, "Invalid flash_family specified")
        return redirect('firmware_flash_select_family')

    return render_with_devices(request, template_name='firmware_flash/test_select_firmware.html',
                               context={'flash_family_id': flash_family.id})
