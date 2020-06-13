from django.shortcuts import render
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth import login
from django.contrib.auth.models import User
from constance import config
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from . import forms, tasks

from app.models import BrewPiDevice
from firmware_flash.models import DeviceFamily, Firmware, Board, get_model_version, check_model_version, FlashRequest, Project

import app.serial_integration as serial_integration

from app.decorators import site_is_configured  # Checks if user has completed constance configuration

import os, subprocess, datetime, pytz

import json


# Fermentrack integration
try:
    from app.models import BrewPiDevice
    FERMENTRACK_INTEGRATION = True
except:
    FERMENTRACK_INTEGRATION = False


@login_required
@site_is_configured
def firmware_select_family(request):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.add_device'):
    #     messages.error(request, 'Your account is not permissioned to add devices. Please contact an admin')
    #     return redirect("/")

    preferred_tz = pytz.timezone(config.PREFERRED_TIMEZONE)

    # If the firmware data is more than 24 hours old, attempt to refresh it
    try:
        # TODO - Remove once python 2 support is gone
        #PYTHON 2 to 3 UPGRADE BUG
        if config.FIRMWARE_LIST_LAST_REFRESHED < timezone.now() - datetime.timedelta(hours=24):
            refresh_firmware()
    except:
        config.FIRMWARE_LIST_LAST_REFRESHED = timezone.now() - datetime.timedelta(hours=72)
        refresh_firmware()


    # Test if avrdude is available. If not, the user will need to install it.
    try:
        rettext = subprocess.check_output(["dpkg", "-s", "avrdude"]).decode(encoding='cp437')
        install_check = rettext.find("installed")

        if install_check == -1:
            # The package status isn't installed
            messages.error(request, "Warning - Package 'avrdude' not installed. Arduino installations will fail! Click <a href=\"http://www.fermentrack.com/help/avrdude/\">here</a> to learn how to resolve this issue.")
    except:
        messages.warning(request, "Unable to check for installed 'avrdude' package - Arduino installations may fail!")

    # Let's delete any requests that are more than 7 days old
    # TODO - Decide if we want to keep things working this way
    requests_to_delete = FlashRequest.objects.filter(created__lt=(timezone.now() - datetime.timedelta(days=7)))

    for this_request in requests_to_delete:
        this_request.delete()

    # Then load the remaining flash requests
    flash_requests = FlashRequest.objects.all().order_by("-created")

    if request.POST:
        form = forms.FirmwareFamilyForm(request.POST)
        if form.is_valid():
            return redirect('firmware_select_board', flash_family_id=form.cleaned_data['device_family'])
            # return redirect('firmware_flash_serial_autodetect', flash_family_id=form.cleaned_data['device_family'])
        else:
            return render(request, template_name='firmware_flash/select_family.html',
                          context={'form': form, 'last_checked': config.FIRMWARE_LIST_LAST_REFRESHED,
                                   'preferred_tz': preferred_tz, 'flash_requests': flash_requests})
    else:
        form = forms.FirmwareFamilyForm()
        return render(request, template_name='firmware_flash/select_family.html',
                      context={'form': form, 'last_checked': config.FIRMWARE_LIST_LAST_REFRESHED,
                               'preferred_tz': preferred_tz, 'flash_requests': flash_requests})


@login_required
@site_is_configured
def firmware_select_board(request, flash_family_id):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.add_device'):
    #     messages.error(request, 'Your account is not permissioned to add devices. Please contact an admin')
    #     return redirect("/")


    try:
        flash_family = DeviceFamily.objects.get(id=flash_family_id)
    except:
        messages.error(request, "Invalid flash_family specified")
        return redirect('firmware_flash_select_family')


    # Test if avrdude is available. If not, the user will need to install it for flashing AVR-based devices.
    if flash_family.flash_method == DeviceFamily.FLASH_ARDUINO:
        try:
            rettext = subprocess.check_output(["dpkg", "-s", "avrdude"]).decode(encoding='cp437')
            install_check = rettext.find("installed")

            if install_check == -1:
                # The package status isn't installed - we explicitly cannot install arduino images
                messages.error(request, "Warning - Package 'avrdude' not installed. Arduino installations will fail! Click <a href=\"http://www.fermentrack.com/help/avrdude/\">here</a> to learn how to resolve this issue.")
                return redirect('firmware_flash_select_family')
        except:
            messages.warning(request, "Unable to check for installed 'avrdude' package - Arduino installations may fail!")
            # Not redirecting here - up to the user to figure out why flashing fails if they keep going.
            # return redirect('firmware_flash_select_family')


    if request.POST:
        form = forms.BoardForm(request.POST)
        form.set_choices(flash_family)
        if form.is_valid():
            return redirect('firmware_flash_serial_autodetect', board_id=form.cleaned_data['board_type'])
        else:
            return render(request, template_name='firmware_flash/select_board.html',
                                       context={'form': form, 'flash_family': flash_family})
    else:
        form = forms.BoardForm()
        form.set_choices(flash_family)
        return render(request, template_name='firmware_flash/select_board.html',
                                   context={'form': form, 'flash_family': flash_family})


def refresh_firmware(request=None):
    # Before we load anything, check to make sure that the model version on fermentrack.com matches the model version
    # that we can support
    if get_model_version() != check_model_version():
        if request is not None:
            messages.error(request, "The firmware information available at fermentrack.com isn't something this " +
                                    "version of Fermentrack can interpret. Please update Fermentrack and try again.")
        return False

    # First, load the device family list
    families_loaded = DeviceFamily.load_from_website()

    if families_loaded:
        # This should be done automatically (via cascading deletes) but breaking it out explicitly here just in case
        Firmware.objects.all().delete()
        Project.objects.all().delete()
        Board.objects.all().delete()

        # And if that worked, load the firmware list
        board_loaded = Board.load_from_website()
        if board_loaded:
            projects_loaded = Project.load_from_website()
            if projects_loaded:
                firmware_loaded = Firmware.load_from_website()
                if firmware_loaded:
                    # Success! Families, Boards, Projects, and Firmware are all loaded
                    config.FIRMWARE_LIST_LAST_REFRESHED = timezone.now()  # Update the "last refreshed" check
                    return firmware_loaded
                else:
                    if request is not None:
                        messages.error(request, "Unable to load firmware from fermentrack.com")
                    return False
            else:
                if request is not None:
                    messages.error(request, "Unable to load projects from fermentrack.com")
                return False
        else:
            if request is not None:
                messages.error(request, "Unable to load boards from fermentrack.com")
            return False
    else:
        # If it didn't work, return False
        if request is not None:
            messages.error(request, "Unable to load families from fermentrack.com")
        return False

    # if request is not None:
    #     messages.success(request, "Firmware list was successfully refreshed from fermentrack.com")



@login_required
@site_is_configured
def firmware_refresh_list(request):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.add_device'):
    #     messages.error(request, 'Your account is not permissioned to add devices. Please contact an admin')
    #     return redirect("/")

    if refresh_firmware(request):
        messages.success(request, "Firmware list was successfully refreshed from Fermentrack.com")
    else:
        messages.error(request, "Firmware list was not able to be refreshed from Fermentrack.com")

    return redirect('firmware_flash_select_family')



# NOTE - This is a modified version of device_guided_serial_autodetect
@login_required
@site_is_configured
def firmware_flash_serial_autodetect(request, board_id):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.add_device'):
    #     messages.error(request, 'Your account is not permissioned to add devices. Please contact an admin')
    #     return redirect("/")

    # device_guided_serial_autodetect contains all 4 steps in the Serial autodetection guided setup.


    try:
        board_obj = Board.objects.get(id=board_id)
    except:
        messages.error(request, "Invalid board ID specified")
        return redirect('firmware_flash_select_family')

    flash_family = board_obj.family

    if not request.POST:
        # If we haven't had something posted to us, provide the instructions page. (Step 1)
        return render(request, template_name='firmware_flash/serial_autodetect_1.html',
                                   context={'board_id': board_id, 'board': board_obj})

    else:
        # Something was posted - figure out what step we're on by looking at the "step" field
        if 'step' not in request.POST:
            # We received a form, but not the right form. Redirect to the start of the autodetection flow.
            return render(request, template_name='firmware_flash/serial_autodetect_1.html',
                                       context={'board_id': board_id, 'board': board_obj})
        elif request.POST['step'] == "2":
            # Step 2 - Cache the current devices & present the next set of instructions to the user
            current_devices = serial_integration.cache_current_devices()
            return render(request, template_name='firmware_flash/serial_autodetect_2.html',
                                       context={'board_id': board_id, 'current_devices': current_devices})
        elif request.POST['step'] == "3":
            # Step 3 - Detect newly-connected devices & prompt the user to select the one that corresponds to the
            # device they want to configure.
            _, _, _, new_devices_enriched = serial_integration.compare_current_devices_against_cache(flash_family.detection_family)
            return render(request, template_name='firmware_flash/serial_autodetect_3.html',
                                       context={'board_id': board_id, 'new_devices': new_devices_enriched})
        else:
            # The step number we received was invalid. Redirect to the start of the autodetection flow.
            return render(request, template_name='setup/device_guided_serial_autodetect_1.html',
                                       context={'board_id': board_id})


@login_required
@site_is_configured
def firmware_flash_select_firmware(request, board_id):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.add_device'):
    #     messages.error(request, 'Your account is not permissioned to add devices. Please contact an admin')
    #     return redirect("/")

    try:
        board_obj = Board.objects.get(id=board_id)
    except:
        messages.error(request, "Invalid board ID specified")
        return redirect('firmware_flash_select_family')

    flash_family = board_obj.family

    if not request.POST:
        # If we weren't passed anything in request.POST, kick the user back to the autodetect routine
        return render(request, template_name='firmware_flash/serial_autodetect_1.html',
                                   context={'board_id': board_id})

    if 'serial_port' not in request.POST:
        # Same if we weren't explicitly passed request.POST['serial_port']
        messages.error(request, "Serial port wasn't provided to 'select_firmware'. Please restart serial autodetection & try again.")
        return render(request, template_name='firmware_flash/serial_autodetect_1.html',
                                   context={'board_id': board_id})


    fermentrack_firmware = Firmware.objects.filter(is_fermentrack_supported=True, in_error=False, family=flash_family).order_by('weight')
    other_firmware = Firmware.objects.filter(is_fermentrack_supported=False, in_error=False, family=flash_family).order_by('weight')
    error_firmware = Firmware.objects.filter(in_error=True, family=flash_family).order_by('weight')

    return render(request, template_name='firmware_flash/select_firmware.html',
                               context={'other_firmware': other_firmware, 'fermentrack_firmware': fermentrack_firmware,
                                        'flash_family': flash_family, 'error_firmware': error_firmware,
                                        'board': board_obj, 'serial_port': request.POST['serial_port']})

@login_required
@site_is_configured
def firmware_flash_flash_firmware(request, board_id):

    try:
        board_obj = Board.objects.get(id=board_id)
    except:
        messages.error(request, "Invalid board ID specified")
        return redirect('firmware_flash_select_family')

    flash_family = board_obj.family

    if not request.POST:
        # If we weren't passed anything in request.POST, kick the user back to the autodetect routine
        return render(request, template_name='firmware_flash/serial_autodetect_1.html',
                                   context={'board_id': board_id})

    if 'serial_port' not in request.POST:
        # Same if we weren't explicitly passed request.POST['serial_port']
        messages.error(request, "Serial port wasn't provided to 'select_firmware'. Please restart serial autodetection & try again.")
        return render(request, template_name='firmware_flash/serial_autodetect_1.html',
                                   context={'board_id': board_id})

    if 'firmware_id' not in request.POST:
        messages.error(request, "Invalid firmware ID was specified! Please restart serial autodetection & try again.")
        return render(request, template_name='firmware_flash/serial_autodetect_1.html',
                                   context={'board_id': board_id})

    try:
        firmware_to_flash = Firmware.objects.get(id=request.POST['firmware_id'])
    except:
        messages.error(request, "Invalid firmware ID was specified! Please restart serial autodetection & try again.")
        return render(request, template_name='firmware_flash/serial_autodetect_1.html',
                                   context={'board_id': board_id})

    # We've been handed everything we need to start flashing the device. Save it to a FlashRequest object & then trigger
    # the huey task.
    flash_request = FlashRequest(
        firmware_to_flash = firmware_to_flash,
        board_type=board_obj,
        serial_port=request.POST['serial_port'],
    )

    flash_request.save()

    req = tasks.flash_firmware(flash_request.id)

    messages.info(request, "Firmware flash has been queued and will be completed shortly.")

    return render(request, template_name='firmware_flash/flash_firmware.html',
                               context={'flash_family': flash_family, 'firmware': firmware_to_flash,
                                        'serial_port': request.POST['serial_port'], 'board': board_obj})

@login_required
@site_is_configured
def firmware_flash_flash_status(request, flash_request_id):
    try:
        flash_request = FlashRequest.objects.get(id=flash_request_id)
    except:
        messages.error(request, "Unable to load flash request with ID {}".format(flash_request_id))
        return redirect('firmware_flash_select_family')

    return render(request, template_name='firmware_flash/flash_status.html', context={'flash_request': flash_request,})

