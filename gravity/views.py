from django.shortcuts import render
from django.contrib import messages
from django.shortcuts import redirect
from constance import config
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
import app.almost_json as almost_json
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ObjectDoesNotExist


import fermentrack_django.settings as settings
from gravity.models import GravitySensor, GravityLog, TiltConfiguration, TiltTempCalibrationPoint, TiltGravityCalibrationPoint, IspindelConfiguration, GravityLogPoint, IspindelGravityCalibrationPoint, TiltBridge

from app.decorators import site_is_configured, login_if_required_for_dashboard, gravity_support_enabled

import os, subprocess, datetime, pytz, json, logging, sys, socket

import gravity.forms as forms

logger = logging.getLogger(__name__)


try:
    # Bluetooth support isn't always available as it requires additional work to install. Going to carve this out to
    # pop up an error message.
    if sys.platform != "darwin":
        import aioblescan
    bluetooth_loaded = True
except ImportError:
    bluetooth_loaded = False


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

                if tilt_form.cleaned_data['connection_type'] == TiltConfiguration.CONNECTION_BRIDGE:
                    if tilt_form.cleaned_data['tiltbridge'] == '+':
                        tilt_bridge = TiltBridge(
                            mdns_id=tilt_form.cleaned_data['tiltbridge_mdns_id'],
                            name=tilt_form.cleaned_data['tiltbridge_name']
                        )
                        tilt_bridge.save()
                        messages.success(request, 'New TiltBridge created')
                    else:
                        tilt_bridge = TiltBridge.objects.get(mdns_id=tilt_form.cleaned_data['tiltbridge'])
                else:
                    # We don't need to link to a bridge, so leave it null
                    tilt_bridge = None

                sensor = GravitySensor(
                    name=tilt_form.cleaned_data['name'],
                    temp_format=tilt_form.cleaned_data['temp_format'],
                    sensor_type=GravitySensor.SENSOR_TILT,
                )
                sensor.save()

                tilt_config = TiltConfiguration(
                    sensor=sensor,
                    color=tilt_form.cleaned_data['color'],
                    connection_type=tilt_form.cleaned_data['connection_type'],
                    tiltbridge=tilt_bridge,
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

        # TODO - Display form validation error message
        messages.error(request, 'Error adding sensor - See below for details')

    # Basically, if we don't get redirected, in every case we're just outputting the same template
    return render(request, template_name='gravity/gravity_add_sensor.html',
                  context={'manual_form': manual_form, 'tilt_form': tilt_form, 'ispindel_form': ispindel_form})


@site_is_configured
@login_if_required_for_dashboard
@gravity_support_enabled
def gravity_list(request):
    # This handles generating the list of grav sensors
    # Loading the actual data for the sensors is handled by Vue.js which loads the data via calls to api/sensors.py

    if not bluetooth_loaded:
        # TODO - Only display this error message when Bluetooth Tilts are present
        messages.warning(request, 'Bluetooth packages for python have not been installed. Tilt support will not work. '
                                  'Click <a href=\"http://www.fermentrack.com/help/bluetooth/\">here</a> to learn how '
                                  'to resolve this issue.')

    all_devices = GravitySensor.objects.all()
    return render(request, template_name="gravity/gravity_list.html", context={'all_devices': all_devices})


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
    except ObjectDoesNotExist:
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
    return render(request, template_name='gravity/gravity_add_point.html', context={'form': form, 'sensor': sensor})


@site_is_configured
@login_if_required_for_dashboard
@gravity_support_enabled
def gravity_dashboard(request, sensor_id, log_id=None):
    try:
        active_device = GravitySensor.objects.get(id=sensor_id)
    except ObjectDoesNotExist:
        messages.error(request, u"Unable to load gravity sensor with ID {}".format(sensor_id))
        return redirect('gravity_list')

    if active_device.sensor_type == GravitySensor.SENSOR_TILT:
        if not bluetooth_loaded and active_device.tilt_configuration.connection_type == TiltConfiguration.CONNECTION_BLUETOOTH:
            messages.warning(request,
                             'Bluetooth packages for python have not been installed. Tilt support will not work. '
                             'Click <a href=\"http://www.fermentrack.com/help/bluetooth/\">here</a> to learn how '
                             'to resolve this issue.')

    log_create_form = forms.GravityLogCreateForm()
    manual_add_form = forms.ManualPointForm()

    if log_id is None:
        active_log = active_device.active_log or None
        available_logs = GravityLog.objects.filter(device_id=active_device.id)  # TODO - Do I want to exclude the active log?
    else:
        try:
            active_log = GravityLog.objects.get(id=log_id, device_id=active_device.id)
        except ObjectDoesNotExist:
            # If we are given an invalid log ID, let's return an error & drop back to the (valid) dashboard
            messages.error(request, u'Unable to load log with ID {}'.format(log_id))
            return redirect('gravity_dashboard', sensor_id=sensor_id)
        available_logs = GravityLog.objects.filter(device_id=active_device.id).exclude(id=log_id)

    if active_log is None:
        # TODO - Determine if we want to load some fake "example" data (similar to what brewpi-www does)
        log_file_url = "/data/gravity_fake.csv"
    else:
        log_file_url = active_log.data_file_url('base_csv')

    return render(request, template_name="gravity/gravity_dashboard.html",
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
    except ObjectDoesNotExist:
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

    return render(request, template_name='gravity/gravity_log_list.html', context={'all_logs': all_logs})


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
        # TODO - Rewrite this to make it more specific (ObjectDoesNotExist error, for example)
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
    except ObjectDoesNotExist:
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
    except ObjectDoesNotExist:
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
    except ObjectDoesNotExist:
        messages.error(request, u'Unable to load sensor with ID {}'.format(sensor_id))
        return redirect('gravity_log_list')

    if request.POST:
        if 'remove_1' in request.POST and 'remove_2' in request.POST and 'remove_3' in request.POST:
            if request.POST['remove_1'] == "on" and request.POST['remove_2'] == "on" and request.POST['remove_3'] == "on":

                if sensor.assigned_brewpi_device is not None:
                    if sensor.assigned_brewpi_device.active_beer is not None:
                        # The temperature sensor is currently actively logging something. Let's stop it.
                        sensor.assigned_brewpi_device.manage_logging('stop')

                try:
                    # If sensor has an attached tiltbridge - cache it so we can delete it if this is the only device that
                    # is connected to it
                    tiltbridge_device = sensor.tilt_configuration.tiltbridge
                except:
                    tiltbridge_device = None

                sensor.delete()

                if tiltbridge_device is not None:
                    if tiltbridge_device.tiltconfiguration_set.count() == 0:
                        # Sure enough, the tiltbridge no longer has any attached devices. Delete it.
                        tiltbridge_device.delete()

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
    except ObjectDoesNotExist:
        messages.error(request, u'Unable to load sensor with ID {}'.format(sensor_id))
        return redirect('gravity_log_list')

    context = {'active_device': sensor}

    if sensor.sensor_type == GravitySensor.SENSOR_ISPINDEL:
        # I am sure there is an easier way to do this, I just can't think of it at the moment
        try:
            initial = {
                'a': sensor.ispindel_configuration.third_degree_coefficient,
                'b': sensor.ispindel_configuration.second_degree_coefficient,
                'c': sensor.ispindel_configuration.first_degree_coefficient,
                'd': sensor.ispindel_configuration.constant_term,
            }
        except ObjectDoesNotExist:
            # The sensor is in an inconsistent state. Delete it.
            messages.error(request, u"The gravity sensor {} had incomplete configuration and was deleted".format(sensor.name))
            sensor.delete()
            return redirect("siteroot")

        ispindel_coefficient_form = forms.IspindelCoefficientForm(initial=initial)
        context['ispindel_coefficient_form'] = ispindel_coefficient_form

        calibration_points = IspindelGravityCalibrationPoint.objects.filter(sensor=sensor.ispindel_configuration).order_by('angle')
        context['ispindel_calibration_points'] = calibration_points
        ispindel_calibration_form = forms.IspindelCalibrationPointForm(initial={'sensor': sensor.ispindel_configuration})
        context['ispindel_calibration_form'] = ispindel_calibration_form

        return render(request, template_name='gravity/gravity_manage_ispindel.html', context=context)

    elif sensor.sensor_type == GravitySensor.SENSOR_TILT:
        # I am sure there is an easier way to do this, I just can't think of it at the moment
        try:
            initial = {
                'b': sensor.tilt_configuration.grav_second_degree_coefficient,
                'c': sensor.tilt_configuration.grav_first_degree_coefficient,
                'd': sensor.tilt_configuration.grav_constant_term,
            }
        except ObjectDoesNotExist:
            # The sensor is in an inconsistent state. Delete it.
            messages.error(request, u"The gravity sensor {} had incomplete configuration and was deleted".format(sensor.name))
            sensor.delete()
            return redirect("siteroot")


        tilt_coefficient_form = forms.TiltCoefficientForm(initial=initial)
        context['tilt_coefficient_form'] = tilt_coefficient_form

        calibration_points = TiltGravityCalibrationPoint.objects.filter(sensor=sensor.tilt_configuration).order_by('tilt_measured_gravity')
        context['tilt_calibration_points'] = calibration_points
        tilt_calibration_form = forms.TiltGravityCalibrationPointForm(initial={'sensor': sensor.tilt_configuration})
        context['tilt_calibration_form'] = tilt_calibration_form

        if sensor.tilt_configuration.connection_type == TiltConfiguration.CONNECTION_BRIDGE:
            # For TiltBridges, we want to give the user the info necessary to configure the device to communicate with
            # Fermentrack
            fermentrack_host = request.META['HTTP_HOST']
            try:
                if ":" in fermentrack_host:
                    fermentrack_host = fermentrack_host[:fermentrack_host.find(":")]
                ais = socket.getaddrinfo(fermentrack_host, 0, 0, 0, 0)
                ip_list = [result[-1][0] for result in ais]
                ip_list = list(set(ip_list))
                resolved_address = ip_list[0]
                fermentrack_url = "http://{}/tiltbridge/".format(resolved_address)
            except:
                # For some reason we failed to resolve the IP address of Fermentrack
                fermentrack_url = "<Error - Unable to resolve Fermentrack IP address>"
            context['fermentrack_url'] = fermentrack_url


        return render(request, template_name='gravity/gravity_manage_tilt.html', context=context)
    else:
        return render(request, template_name='gravity/gravity_manage.html', context=context)


# So here's the deal -- If we want to write json files sequentially, we have to skip closing the array. If we want to
# then interpret them using JavaScript, however, we MUST have fully formed, valid json. To acheive that, we're going to
# wrap the json file and append the closing bracket after dumping its contents to the browser.
def almost_json_view(request, sensor_id, log_id):
    json_close = "\r\n]"

    # gravity_log = GravityLog.objects.get(id=log_id, device_id=sensor_id)
    gravity_log = GravityLog.objects.get(id=log_id)

    filename = os.path.join(settings.BASE_DIR, settings.DATA_ROOT, gravity_log.full_filename("annotation_json"))

    if os.path.isfile(filename):  # If there are no annotations, return an empty JsonResponse
        f = open(filename, 'r')
        wrapper = almost_json.AlmostJsonWrapper(f, closing_string=json_close)
        response = HttpResponse(wrapper, content_type="application/json")
        response['Content-Length'] = os.path.getsize(filename) + len(json_close)
        return response
    else:
        empty_array = []
        return JsonResponse(empty_array, safe=False, json_dumps_params={'indent': 4})
