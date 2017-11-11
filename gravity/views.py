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

from app.decorators import site_is_configured, login_if_required_for_dashboard, gravity_support_enabled

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
@gravity_support_enabled
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
@gravity_support_enabled
def gravity_list(request):
    # This handles generating the list of grav sensors
    # Loading the actual data for the sensors is handled by Vue.js which loads the data via calls to api/sensors.py
    return render_with_devices(request, template_name="gravity/gravity_list.html")

@login_required
@site_is_configured
@gravity_support_enabled
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
@gravity_support_enabled
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
@gravity_support_enabled
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


@login_required
@site_is_configured
@gravity_support_enabled
def gravity_log_list(request):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.add_beer'):
    #     messages.error(request, 'Your account is not permissioned to add beers. Please contact an admin')
    #     return redirect("/")

    all_logs = GravityLog.objects.all().order_by('device').order_by('name')

    return render_with_devices(request, template_name='gravity/gravity_log_list.html', context={'all_logs': all_logs})


@login_required
@site_is_configured
@gravity_support_enabled
def gravity_log_delete(request, log_id):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.add_beer'):
    #     messages.error(request, 'Your account is not permissioned to add beers. Please contact an admin')
    #     return redirect("/")

    try:
        log_obj = GravityLog.objects.get(id=log_id)

        if log_obj.device:
            if log_obj.device.active_log == log_obj:
                # If the log is currently being logged to, we don't want to trigger a delete
                messages.error(request, u'Requested log is currently in use - Stop logging on device and reattempt')
                return redirect('gravity_log_list')

        log_obj.delete()
        messages.success(request, u'Log "{}" was deleted'.format(log_obj.name))
    except:
        messages.error(request, u'Unable to delete log with ID {}'.format(log_id))
    return redirect('gravity_log_list')


@login_required
@site_is_configured
@gravity_support_enabled
def gravity_attach(request, sensor_id):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.add_beer'):
    #     messages.error(request, 'Your account is not permissioned to add beers. Please contact an admin')
    #     return redirect("/")

    try:
        sensor = GravitySensor.objects.get(id=sensor_id)
    except:
        messages.error(request, u'Unable to load sensor with ID {}'.format(sensor_id))
        return redirect('gravity_log_list')

    if sensor.assigned_brewpi_device is not None:
        messages.error(request, u'Device {} already has an assigned temperature controller'.format(str(sensor)))
        return redirect('gravity_dashboard', sensor_id=sensor_id)


    form = forms.SensorAttachForm()
    if request.POST:
        form = forms.SensorAttachForm(request.POST)
        if form.is_valid():

            # If the form is valid, we know a couple of things:
            # 1. That the device is unbound
            # 2. That the sensor is unbound
            # ...but we DON'T know if either device is actively logging.

            # Breaking this out for ease of use
            form_sensor = GravitySensor.objects.get(id=form.cleaned_data['sensor'].id)

            if form_sensor.active_log is not None:
                # The gravity sensor is currently actively logging something. This is not ideal. Lets stop it.
                form_sensor.active_log = None
                messages.warning(request, "Gravity sensor {} was actively logging, but has now been stopped.".format(form_sensor))
                # We'll save in a bit

            if form.cleaned_data['temp_controller'].active_beer is not None:
                # The temperature sensor is currently actively logging something. This is not ideal. Lets stop it.
                form.cleaned_data['temp_controller'].manage_logging('stop')
                # The save on this one is embedded in the manage_logging method
                messages.warning(request, "Controller {} was actively logging, but has now been stopped.".format(form.cleaned_data['temp_controller']))

            form_sensor.assigned_brewpi_device = form.cleaned_data['temp_controller']
            form_sensor.save()

            messages.success(request, "Succesfully assigned sensor {} to temperature controller {}".format(form_sensor, form.cleaned_data['temp_controller']))
            return redirect('gravity_dashboard', sensor_id=sensor_id)

            # else:
        #     messages.error(request, "Invalid " % form.errors['__all__'])


    return render(request, template_name='gravity/gravity_attach.html', context={'selected_sensor': sensor, 'form': form})



@login_required
@site_is_configured
@gravity_support_enabled
def gravity_detach(request, sensor_id):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.add_beer'):
    #     messages.error(request, 'Your account is not permissioned to add beers. Please contact an admin')
    #     return redirect("/")

    try:
        sensor = GravitySensor.objects.get(id=sensor_id)
    except:
        messages.error(request, u'Unable to load sensor with ID {}'.format(sensor_id))
        return redirect('gravity_log_list')

    if sensor.assigned_brewpi_device is None:
        messages.error(request, u'Device {} is already detached from any temperature controller'.format(str(sensor)))
        return redirect('gravity_dashboard', sensor_id=sensor_id)

    if sensor.assigned_brewpi_device.active_beer is not None:
        # The temperature sensor is currently actively logging something. Let's stop it. This will also stop the logging
        # for the gravity sensor.
        sensor.assigned_brewpi_device.manage_logging('stop')
        # The save on this one is embedded in the manage_logging method
        messages.warning(request, "Controller {} was actively logging, and has now been stopped.".format(sensor.assigned_brewpi_device))

    sensor.assigned_brewpi_device = None
    sensor.save()

    messages.success(request, "Succesfully detached sensor {} from temperature controller".format(sensor))
    return redirect('gravity_dashboard', sensor_id=sensor_id)
