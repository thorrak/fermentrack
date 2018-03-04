from django.shortcuts import render
from django.contrib import messages
from django.shortcuts import render_to_response, redirect
from django.contrib.auth import login
from django.contrib.auth.models import User
from constance import config
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json, socket
from django.http import JsonResponse

from app.models import BrewPiDevice
from gravity.models import GravitySensor, GravityLog, TiltConfiguration, TiltTempCalibrationPoint, TiltGravityCalibrationPoint, IspindelConfiguration, GravityLogPoint, IspindelGravityCalibrationPoint

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
    tilt_form = forms.TiltCreateForm()
    ispindel_form = forms.IspindelCreateForm()

    if request.POST:
        if request.POST['sensor_family'] == "manual":
            manual_form = forms.ManualForm(request.POST)
            if manual_form.is_valid():
                sensor = manual_form.save()
                messages.success(request, 'New manual sensor added')

                return redirect('gravity_list')

        elif request.POST['sensor_family'] == "tilt":
            tilt_form = forms.TiltCreateForm(request.POST)
            if tilt_form.is_valid():
                sensor = GravitySensor(
                    name=tilt_form.cleaned_data['name'],
                    temp_format=tilt_form.cleaned_data['temp_format'],
                    sensor_type=GravitySensor.SENSOR_TILT,
                )
                sensor.save()

                tilt_config = TiltConfiguration(
                    sensor=sensor,
                    color=tilt_form.cleaned_data['color'],
                )
                tilt_config.save()
                messages.success(request, 'New tilt sensor added')

                return redirect('gravity_list')

        elif request.POST['sensor_family'] == "ispindel":
            ispindel_form = forms.IspindelCreateForm(request.POST)
            if ispindel_form.is_valid():
                sensor = GravitySensor(
                    name=ispindel_form.cleaned_data['name'],
                    temp_format=ispindel_form.cleaned_data['temp_format'],
                    sensor_type=GravitySensor.SENSOR_ISPINDEL,
                )
                sensor.save()

                ispindel_config = IspindelConfiguration(
                    sensor=sensor,
                    name_on_device=ispindel_form.cleaned_data['name_on_device'],
                )
                ispindel_config.save()

                messages.success(request, 'New iSpindel sensor added')

                return redirect('gravity_ispindel_setup', sensor_id=sensor.id)

        messages.error(request, 'Error adding sensor')

    # Basically, if we don't get redirected, in every case we're just outputting the same template
    return render_with_devices(request, template_name='gravity/gravity_family.html',
                               context={'manual_form': manual_form, 'tilt_form': tilt_form,
                                        'ispindel_form': ispindel_form})


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
        messages.error(request, u'Unable to load sensor with ID {}'.format(manual_sensor_id))
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


@site_is_configured
@login_if_required_for_dashboard
@gravity_support_enabled
def gravity_dashboard(request, sensor_id, log_id=None):
    try:
        active_device = GravitySensor.objects.get(id=sensor_id)
    except:
        messages.error(request, u"Unable to load gravity sensor with ID {}".format(sensor_id))
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
            messages.error(request, u'Unable to load log with ID {}'.format(log_id))
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
                    u"Successfully created log '{}'.<br>Graph will not appear until the first log points \
                    have been collected. You will need to refresh the page for it to \
                    appear.".format(form.cleaned_data['log_name']))
            else:
                messages.success(request, u"Log {} already exists - assigning to device".format(form.cleaned_data['log_name']))

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
def gravity_log_stop(request, sensor_id):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.add_beer'):
    #     messages.error(request, 'Your account is not permissioned to add gravity logs. Please contact an admin')
    #     return redirect("/")

    try:
        sensor = GravitySensor.objects.get(id=sensor_id)
    except:
        messages.error(request, u'Unable to load sensor with ID {}'.format(sensor_id))
        return redirect('gravity_log_list')

    if sensor.active_log:
        # We'll stop logging -- but only if the sensor isn't attached to a BrewPiDevice
        if sensor.assigned_brewpi_device is not None:
            messages.error(request, u'This sensor is currently assigned to a temperature controller. Please stop '
                                    u'logging for that temperature controller to stop logging for this sensor.')
        else:
            sensor.active_log = None
            sensor.save()
            messages.success(request, u'Logging has been stopped for sensor {}'.format(sensor))

    else:
        messages.error(request, u'Unable to stop logging as that sensor wasn\'t actively logging something')

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
                messages.warning(request, u"Gravity sensor {} was actively logging, but has now been stopped.".format(form_sensor))
                # We'll save in a bit

            if form.cleaned_data['temp_controller'].active_beer is not None:
                # The temperature sensor is currently actively logging something. This is not ideal. Lets stop it.
                form.cleaned_data['temp_controller'].manage_logging('stop')
                # The save on this one is embedded in the manage_logging method
                messages.warning(request, u"Controller {} was actively logging, but has now been stopped.".format(form.cleaned_data['temp_controller']))

            form_sensor.assigned_brewpi_device = form.cleaned_data['temp_controller']
            form_sensor.save()

            messages.success(request, u"Succesfully assigned sensor {} to temperature controller {}".format(form_sensor, form.cleaned_data['temp_controller']))
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
        messages.warning(request, u"Controller {} was actively logging, and has now been stopped.".format(sensor.assigned_brewpi_device))

    sensor.assigned_brewpi_device = None
    sensor.save()

    messages.success(request, u"Succesfully detached sensor {} from temperature controller".format(sensor))
    return redirect('gravity_dashboard', sensor_id=sensor_id)


@login_required
@site_is_configured
@gravity_support_enabled
def gravity_uninstall(request, sensor_id):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.delete_device'):
    #     messages.error(request, 'Your account is not permissioned to uninstall devices. Please contact an admin')
    #     return redirect("/")

    try:
        sensor = GravitySensor.objects.get(id=sensor_id)
    except:
        messages.error(request, u'Unable to load sensor with ID {}'.format(sensor_id))
        return redirect('gravity_log_list')

    if request.POST:
        if 'remove_1' in request.POST and 'remove_2' in request.POST and 'remove_3' in request.POST:
            if request.POST['remove_1'] == "on" and request.POST['remove_2'] == "on" and request.POST['remove_3'] == "on":

                if sensor.assigned_brewpi_device is not None:
                    if sensor.assigned_brewpi_device.active_beer is not None:
                        # The temperature sensor is currently actively logging something. Let's stop it.
                        sensor.assigned_brewpi_device.manage_logging('stop')

                sensor.delete()
                messages.success(request, u"The device '{}' was successfully uninstalled.".format(sensor))
                return redirect("siteroot")

        # If we get here, one of the switches wasn't toggled
        messages.error(request, "All three switches must be set to 'yes' to uninstall a sensor.")
        return redirect("gravity_manage", sensor_id=sensor_id)
    else:
        messages.error(request, "To uninstall a device, use the form on the 'Manage Sensor' page.")
        return redirect("gravity_manage", sensor_id=sensor_id)




@login_required
@site_is_configured
def gravity_manage(request, sensor_id):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.edit_device'):
    #     messages.error(request, 'Your account is not permissioned to edit devices. Please contact an admin')
    #     return redirect("/")

    try:
        sensor = GravitySensor.objects.get(id=sensor_id)
    except:
        messages.error(request, u'Unable to load sensor with ID {}'.format(sensor_id))
        return redirect('gravity_log_list')

    context = {'active_device': sensor}

    if sensor.sensor_type == 'ispindel':
        # I am sure there is an easier way to do this, I just can't think of it at the moment
        initial = {'a': sensor.ispindel_configuration.third_degree_coefficient,
                   'b': sensor.ispindel_configuration.second_degree_coefficient,
                   'c': sensor.ispindel_configuration.first_degree_coefficient,
                   'd': sensor.ispindel_configuration.constant_term,
                   }
        ispindel_coefficient_form = forms.IspindelCoefficientForm(initial=initial)
        context['ispindel_coefficient_form'] = ispindel_coefficient_form

        calibration_points = IspindelGravityCalibrationPoint.objects.filter(sensor=sensor)
        context['ispindel_calibration_points'] = calibration_points
        ispindel_calibration_form = forms.IspindelGravityCalibrationPoint()
        context['ispindel_calibration_form'] = ispindel_calibration_form

    return render(request, template_name='gravity/gravity_manage.html', context=context)


@login_required
@site_is_configured
def gravity_ispindel_setup(request, sensor_id):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.edit_device'):
    #     messages.error(request, 'Your account is not permissioned to edit devices. Please contact an admin')
    #     return redirect("/")

    try:
        sensor = GravitySensor.objects.get(id=sensor_id)
    except:
        messages.error(request, u'Unable to load sensor with ID {}'.format(sensor_id))
        return redirect('gravity_log_list')

    if sensor.sensor_type != "ispindel":
        messages.error(request, u"Sensor {} is not an iSpindel sensor".format(sensor.name))
        return redirect('gravity_log_list')

    # When we're configuring the iSpindel sensor, we need to tell it how to connect back to Fermentrack. Get the
    # hostname, port, and IP address here so we can provide it to the user to enter.
    fermentrack_host = request.META['HTTP_HOST']
    try:
        ais = socket.getaddrinfo(fermentrack_host, 0, 0, 0, 0)
        ip_list = [result[-1][0] for result in ais]
        ip_list = list(set(ip_list))
        resolved_address = ip_list[0]
    except:
        # For some reason we failed to resolve the IP address of this host. Let's let the user know they'll have to
        # figure it out.
        resolved_address = "<The IP address of Fermentrack> (Unable to autodetect. Sorry.)"

    return render(request, template_name='gravity/gravity_ispindel_setup.html',
                  context={'active_device': sensor, 'fermentrack_host': fermentrack_host,
                           'fermentrack_ip': resolved_address})


@csrf_exempt
def ispindel_handler(request):
    if request.body is None:
        # TODO - Log this
        return JsonResponse({'status': 'failed', 'message': "No data in request body"}, safe=False,
                            json_dumps_params={'indent': 4})

    # import pprint
    # with open('ispindel_json_output.txt', 'w') as logFile:
    #     pprint.pprint(ispindel_data, logFile)

    # As of the iSpindel firmware version 5.6.1, the json posted contains the following fields:
    # {u'ID': 3003098,
    #  u'angle': 77.4576,
    #  u'battery': 4.171011,
    #  u'gravity': 27.22998,
    #  u'name': u'iSpindel123',
    #  u'temperature': 24.75,
    #  u'token': u'tokengoeshere'}

    ispindel_data = json.loads(request.body)

    try:
        sensor = IspindelConfiguration.objects.get(name_on_device=ispindel_data['name'])
    except:
        # TODO - Log This
        messages.error(request, u'Unable to load sensor with name {}'.format(ispindel_data['name']))
        return JsonResponse({'status': 'failed', 'message': "Unable to load sensor with that name"}, safe=False,
                            json_dumps_params={'indent': 4})


    # Let's calculate the gravity using the coefficients stored in the ispindel configuration. This will allow us to
    # reconfigure on the fly.
    calculated_gravity = sensor.third_degree_coefficient * (ispindel_data['angle']**3)
    calculated_gravity += sensor.second_degree_coefficient * (ispindel_data['angle']**2)
    calculated_gravity += sensor.first_degree_coefficient * (ispindel_data['angle'])
    calculated_gravity += sensor.constant_term

    new_point = GravityLogPoint(
        gravity=calculated_gravity,         # We're using the gravity we calc within Fermentrack
        temp=ispindel_data['temperature'],
        temp_format='C',                    # iSpindel devices always report temp in celsius
        temp_is_estimate=False,
        associated_device=sensor.sensor,
        gravity_latest=calculated_gravity,
        temp_latest=ispindel_data['temperature'],
        extra_data=ispindel_data['angle'],
    )

    if sensor.sensor.active_log is not None:
        new_point.associated_log = sensor.sensor.active_log

    new_point.save()

    # Set & save the 'extra' data points to redis (so we can load & use later)
    if 'angle' in ispindel_data:
        sensor.angle = ispindel_data['angle']
    if 'ID' in ispindel_data:
        sensor.ispindel_id = ispindel_data['ID']
    if 'battery' in ispindel_data:
        sensor.battery = ispindel_data['battery']
    if 'gravity' in ispindel_data:
        sensor.ispindel_gravity = ispindel_data['gravity']
    if 'token' in ispindel_data:
        sensor.token = ispindel_data['token']
    sensor.save_extras_to_redis()

    return JsonResponse({'status': 'ok', 'gravity': calculated_gravity}, safe=False, json_dumps_params={'indent': 4})


@login_required
@site_is_configured
def gravity_ispindel_coefficients(request, sensor_id):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.edit_device'):
    #     messages.error(request, 'Your account is not permissioned to edit devices. Please contact an admin')
    #     return redirect("/")

    try:
        sensor = GravitySensor.objects.get(id=sensor_id)
    except:
        messages.error(request, u'Unable to load sensor with ID {}'.format(sensor_id))
        return redirect('gravity_log_list')

    if request.POST:
        ispindel_coefficient_form = forms.IspindelCoefficientForm(request.POST)
        if ispindel_coefficient_form.is_valid():
            sensor.ispindel_configuration.third_degree_coefficient = ispindel_coefficient_form.cleaned_data['a']
            sensor.ispindel_configuration.second_degree_coefficient = ispindel_coefficient_form.cleaned_data['b']
            sensor.ispindel_configuration.first_degree_coefficient = ispindel_coefficient_form.cleaned_data['c']
            sensor.ispindel_configuration.constant_term = ispindel_coefficient_form.cleaned_data['d']

            sensor.ispindel_configuration.save()
            messages.success(request, u"Coefficients updated")

        else:
            messages.error(request, u"Invalid coefficients provided")
    else:
        messages.error(request, u"No coefficients provided")

    return redirect("gravity_manage", sensor_id=sensor_id)


@login_required
@site_is_configured
def gravity_ispindel_calibration(request, sensor_id):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.edit_device'):
    #     messages.error(request, 'Your account is not permissioned to edit devices. Please contact an admin')
    #     return redirect("/")

    try:
        sensor = GravitySensor.objects.get(id=sensor_id)
    except:
        messages.error(request, u'Unable to load sensor with ID {}'.format(sensor_id))
        return redirect('gravity_log_list')

    if request.POST:
        ispindel_coefficient_form = forms.IspindelCoefficientForm(request.POST)
        if ispindel_coefficient_form.is_valid():
            sensor.ispindel_configuration.third_degree_coefficient = ispindel_coefficient_form.cleaned_data['a']
            sensor.ispindel_configuration.second_degree_coefficient = ispindel_coefficient_form.cleaned_data['b']
            sensor.ispindel_configuration.first_degree_coefficient = ispindel_coefficient_form.cleaned_data['c']
            sensor.ispindel_configuration.constant_term = ispindel_coefficient_form.cleaned_data['d']

            sensor.ispindel_configuration.save()
            messages.success(request, u"Coefficients updated")

        else:
            messages.error(request, u"Invalid coefficients provided")
    else:
        messages.error(request, u"No coefficients provided")

    return redirect("gravity_manage", sensor_id=sensor_id)
