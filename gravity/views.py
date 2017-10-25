from django.shortcuts import render
from django.contrib import messages
from django.shortcuts import render_to_response, redirect
from django.contrib.auth import login
from django.contrib.auth.models import User
from constance import config
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from app.models import BrewPiDevice
from gravity.models import GravitySensor, GravityLog

from app.decorators import site_is_configured, login_if_required_for_dashboard

import os, subprocess, datetime, pytz

import gravity.forms as forms


def render_with_devices(request, template_name, context=None, content_type=None, status=None, using=None):
    all_devices = BrewPiDevice.objects.all()

    if context:  # Append to the context dict if it exists, otherwise create the context dict to add
        context['all_devices'] = all_devices
    else:
        context={'all_devices': all_devices}

    return render(request, template_name, context, content_type, status, using)





@login_required
@site_is_configured
def gravity_add_board(request):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.add_device'):
    #     messages.error(request, 'Your account is not permissioned to add devices. Please contact an admin')
    #     return redirect("/")

    manual_form = forms.ManualForm()

    if request.POST:
        if request.POST['sensor_family'] == "manual":
            manual_form = forms.ManualForm(request.POST)
            if manual_form.is_valid():

                sensor = manual_form.save()
                messages.success(request, 'Sensor added')

                return redirect('gravity_list')
        messages.error(request, 'Error adding sensor')

    # Basically, if we don't get redirected, in every case we're just outputting the same template
    return render_with_devices(request, template_name='gravity/gravity_family.html',
                               context={'manual_form': manual_form,})


@site_is_configured
@login_if_required_for_dashboard
def gravity_list(request):
    # This handles generating the list of grav sensors
    # Loading the actual data for the sensors is handled by Vue.js which loads the data via calls to api/sensors.py
    return render_with_devices(request, template_name="gravity/gravity_list.html")

@login_required
@site_is_configured
def gravity_add_point(request, manual_sensor_id):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.add_device'):
    #     messages.error(request, 'Your account is not permissioned to add devices. Please contact an admin')
    #     return redirect("/")

    try:
        sensor = GravitySensor.objects.get(id=manual_sensor_id)
    except:
        messages.error(request,'Unable to load sensor with ID {}'.format(manual_sensor_id))
        return redirect('gravity_list')

    form = forms.ManualPointForm()

    if request.POST:
        form = forms.ManualPointForm(request.POST)
        if form.is_valid():
            # Generate the new point (but don't save)
            new_point = form.save(commit=False)
            if sensor.active_log is not None:
                new_point.associated_log = sensor.active_log
            else:
                new_point.associated_device = sensor

            new_point.save()

            messages.success(request, 'Successfully added manual log point')

            if 'redirect' in form.data:
                return redirect('gravity_dashboard', sensor_id=manual_sensor_id)
            return redirect('gravity_list')

        messages.error(request, 'Unable to add new manual log point')

    # Basically, if we don't get redirected, in every case we're just outputting the same template
    return render_with_devices(request, template_name='gravity/gravity_add_point.html',
                               context={'form': form, 'sensor': sensor})


        #
    #
    # try:
    #     flash_family = DeviceFamily.objects.get(id=flash_family_id)
    # except:
    #     messages.error(request, "Invalid flash_family specified")
    #     return redirect('firmware_flash_select_family')
    #
    #
    # # Test if avrdude is available. If not, the user will need to install it for flashing AVR-based devices.
    # if flash_family.flash_method == DeviceFamily.FLASH_ARDUINO:
    #     try:
    #         rettext = subprocess.check_output(["dpkg", "-s", "avrdude"])
    #         install_check = rettext.find("installed")
    #
    #         if install_check == -1:
    #             # The package status isn't installed - we explicitly cannot install arduino images
    #             messages.error(request, "Warning - Package 'avrdude' not installed. Arduino installations will fail! Click <a href=\"http://www.fermentrack.com/help/avrdude/\">here</a> to learn how to resolve this issue.")
    #             return redirect('firmware_flash_select_family')
    #     except:
    #         messages.error(request, "Unable to check for installed 'avrdude' package - Arduino installations may fail!")
    #         # Not redirecting here - up to the user to figure out why flashing fails if they keep going.
    #         # return redirect('firmware_flash_select_family')
    #
    #
    # if request.POST:
    #     form = forms.BoardForm(request.POST)
    #     form.set_choices(flash_family)
    #     if form.is_valid():
    #         return redirect('firmware_flash_serial_autodetect', board_id=form.cleaned_data['board_type'])
    #     else:
    #         return render_with_devices(request, template_name='firmware_flash/select_board.html',
    #                                    context={'form': form, 'flash_family': flash_family})
    # else:
    #     form = forms.BoardForm()
    #     form.set_choices(flash_family)
    #     return render_with_devices(request, template_name='firmware_flash/select_board.html',
    #                                context={'form': form, 'flash_family': flash_family})
    #




@site_is_configured
@login_if_required_for_dashboard
def gravity_dashboard(request, sensor_id, log_id=None):
    try:
        active_device = GravitySensor.objects.get(id=sensor_id)
    except:
        messages.error(request, "Unable to load gravity sensor with ID {}".format(sensor_id))
        return redirect('gravity_list')

    log_create_form = forms.GravityLogCreateForm()
    manual_add_form = forms.ManualPointForm()

    if log_id is None:
        active_log = active_device.active_log or None
        available_logs = GravityLog.objects.filter(device_id=active_device.id)  # TODO - Do I want to exclude the active log?
    else:
        try:
            active_log = GravityLog.objects.get(id=log_id, device_id=active_device.id)
        except:
            # If we are given an invalid log ID, let's return an error & drop back to the (valid) dashboard
            messages.error(request, 'Unable to load log with ID {}'.format(log_id))
            return redirect('gravity_dashboard', sensor_id=sensor_id)
        available_logs = GravityLog.objects.filter(device_id=active_device.id).exclude(id=log_id)

    if active_log is None:
        # TODO - Determine if we want to load some fake "example" data (similar to what brewpi-www does)
        log_file_url = "/data/gravity_fake.csv"
    else:
        log_file_url = active_log.data_file_url('base_csv')

    return render_with_devices(request, template_name="gravity/gravity_dashboard.html",
                               context={'active_device': active_device, 'log_create_form': log_create_form,
                                        'active_log': active_log, 'temp_display_format': config.DATE_TIME_FORMAT_DISPLAY,
                                        'column_headers': GravityLog.column_headers_to_graph_string('base_csv'),
                                        'log_file_url': log_file_url, 'available_logs': available_logs,
                                        'selected_log_id': log_id, 'manual_add_form': manual_add_form})



@login_required
@site_is_configured
def gravity_log_create(request, sensor_id):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.add_beer'):
    #     messages.error(request, 'Your account is not permissioned to add gravity logs. Please contact an admin')
    #     return redirect("/")

    # This view is only intended to process data posted, generally from gravity_dashboard. Redirect to the dashboard
    # if we are accessed directly without post data.
    if request.POST:
        form = forms.GravityLogCreateForm(request.POST)
        if form.is_valid():
            new_log, created = GravityLog.objects.get_or_create(name=form.cleaned_data['log_name'],
                                                                 device=form.cleaned_data['device'])
            if created:
                # If we just created the log, set the temp format (otherwise, defaults to Fahrenheit)
                new_log.format = form.cleaned_data['device'].temp_format
                new_log.save()
                messages.success(request,
                    "Successfully created log '{}'.<br>Graph will not appear until the first log points \
                    have been collected. You will need to refresh the page for it to \
                    appear.".format(form.cleaned_data['log_name']))
            else:
                messages.success(request, "Log {} already exists - assigning to device".format(form.cleaned_data['log_name']))

            if form.cleaned_data['device'].active_log != new_log:
                form.cleaned_data['device'].active_log = new_log
                form.cleaned_data['device'].save()

        else:
            messages.error(request, "<p>Unable to create log</p> %s" % form.errors['__all__'])

    # In all cases, redirect to device dashboard
    return redirect('gravity_dashboard', sensor_id=sensor_id)



















def refresh_firmware(request=None):
    # Before we load anything, check to make sure that the model version on fermentrack.com matches the model version
    # that we can support
    if get_model_version() != check_model_version():
        if request is not None:
            messages.error(request, "The firmware information available at fermentrack.com isn't something this " +
                                    "version of Fermentrack can interpret. Please update and try again.")
        return False

    # First, load the device family list
    families_loaded = DeviceFamily.load_from_website()

    if families_loaded:
        # And if that worked, load the firmware list
        board_loaded = Board.load_from_website()
        if board_loaded:
            firmware_loaded = Firmware.load_from_website()
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

    config.FIRMWARE_LIST_LAST_REFRESHED = timezone.now()  # Update the "last refreshed" check
    return firmware_loaded


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
        return render_with_devices(request, template_name='firmware_flash/serial_autodetect_1.html',
                                   context={'board_id': board_id, 'board': board_obj})

    else:
        # Something was posted - figure out what step we're on by looking at the "step" field
        if 'step' not in request.POST:
            # We received a form, but not the right form. Redirect to the start of the autodetection flow.
            return render_with_devices(request, template_name='firmware_flash/serial_autodetect_1.html',
                                       context={'board_id': board_id})
        elif request.POST['step'] == "2":
            # Step 2 - Cache the current devices & present the next set of instructions to the user
            current_devices = serial_integration.cache_current_devices()
            return render_with_devices(request, template_name='firmware_flash/serial_autodetect_2.html',
                                       context={'board_id': board_id, 'current_devices': current_devices})
        elif request.POST['step'] == "3":
            # Step 3 - Detect newly-connected devices & prompt the user to select the one that corresponds to the
            # device they want to configure.
            _, _, _, new_devices_enriched = serial_integration.compare_current_devices_against_cache(flash_family.detection_family)
            return render_with_devices(request, template_name='firmware_flash/serial_autodetect_3.html',
                                       context={'board_id': board_id, 'new_devices': new_devices_enriched})
        else:
            # The step number we received was invalid. Redirect to the start of the autodetection flow.
            return render_with_devices(request, template_name='setup/device_guided_serial_autodetect_1.html',
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
        return render_with_devices(request, template_name='firmware_flash/serial_autodetect_1.html',
                                   context={'board_id': board_id})

    if 'serial_port' not in request.POST:
        # Same if we weren't explicitly passed request.POST['serial_port']
        messages.error(request, "Serial port wasn't provided to 'select_firmware'. Please restart serial autodetection & try again.")
        return render_with_devices(request, template_name='firmware_flash/serial_autodetect_1.html',
                                   context={'board_id': board_id})


    fermentrack_firmware = Firmware.objects.filter(is_fermentrack_supported=True, in_error=False, family=flash_family).order_by('weight')
    other_firmware = Firmware.objects.filter(is_fermentrack_supported=False, in_error=False, family=flash_family).order_by('weight')
    error_firmware = Firmware.objects.filter(in_error=True, family=flash_family).order_by('weight')

    return render_with_devices(request, template_name='firmware_flash/select_firmware.html',
                               context={'other_firmware': other_firmware, 'fermentrack_firmware': fermentrack_firmware,
                                        'flash_family': flash_family, 'error_firmware': error_firmware,
                                        'board': board_obj, 'serial_port': request.POST['serial_port']})
import json

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
        return render_with_devices(request, template_name='firmware_flash/serial_autodetect_1.html',
                                   context={'board_id': board_id})

    if 'serial_port' not in request.POST:
        # Same if we weren't explicitly passed request.POST['serial_port']
        messages.error(request, "Serial port wasn't provided to 'select_firmware'. Please restart serial autodetection & try again.")
        return render_with_devices(request, template_name='firmware_flash/serial_autodetect_1.html',
                                   context={'board_id': board_id})

    if 'firmware_id' not in request.POST:
        messages.error(request, "Invalid firmware ID was specified! Please restart serial autodetection & try again.")
        return render_with_devices(request, template_name='firmware_flash/serial_autodetect_1.html',
                                   context={'board_id': board_id})

    try:
        firmware_to_flash = Firmware.objects.get(id=request.POST['firmware_id'])
    except:
        messages.error(request, "Invalid firmware ID was specified! Please restart serial autodetection & try again.")
        return render_with_devices(request, template_name='firmware_flash/serial_autodetect_1.html',
                                   context={'board_id': board_id})

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
            flash_cmd = ["esptool.py"]
        elif firmware_to_flash.family.flash_method == DeviceFamily.FLASH_ARDUINO:
            flash_cmd = ["avrdude"]
        else:
            messages.error(request, "Selected device family is unsupported in this version of Fermentrack!")
            return redirect('firmware_flash_select_family')

        flash_args = json.loads(board_obj.flash_options_json)

        for arg in flash_args:
            flash_cmd.append(str(arg).replace("{serial_port}", request.POST['serial_port']).replace("{firmware_path}", firmware_path))


        # TODO - Explicitly need to disable any device on that port
        if FERMENTRACK_INTEGRATION:
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
                                        'flash_cmd': flash_cmd, 'device_flashed': device_flashed,
                                        'board': board_obj})




# TODO - Delete this view
# @login_required
# @site_is_configured
# def firmware_flash_test_select_firmware(request):
#     try:
#         flash_family = DeviceFamily.objects.get(name="ESP8266")
#     except:
#         messages.error(request, "Invalid flash_family specified")
#         return redirect('firmware_flash_select_family')
#
#     return render_with_devices(request, template_name='firmware_flash/test_select_firmware.html',
#                                context={'flash_family_id': flash_family.id})
