from django.shortcuts import render
from django.contrib import messages
from django.shortcuts import render_to_response, redirect
from django.contrib.auth import login
from django.contrib.auth.models import User
from constance import config
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json, socket, decimal
from django.http import JsonResponse

from app.models import BrewPiDevice
from gravity.models import GravitySensor, GravityLog, IspindelConfiguration, GravityLogPoint, IspindelGravityCalibrationPoint

from app.decorators import site_is_configured, login_if_required_for_dashboard, gravity_support_enabled

import os, subprocess, datetime, pytz

import gravity.forms as forms



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

    if sensor.sensor_type != GravitySensor.SENSOR_ISPINDEL:
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
    calculated_gravity = sensor.third_degree_coefficient * decimal.Decimal(ispindel_data['angle']**3)
    calculated_gravity += sensor.second_degree_coefficient * decimal.Decimal(ispindel_data['angle']**2)
    calculated_gravity += sensor.first_degree_coefficient * decimal.Decimal(ispindel_data['angle'])
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

    if sensor.sensor_type != GravitySensor.SENSOR_ISPINDEL:
        messages.error(request, u'Sensor {} is not an iSpindel and cannot be configured in this way!'.format(sensor_id))
        return redirect('gravity_log_list')


    if request.POST:
        ispindel_coefficient_form = forms.IspindelCoefficientForm(request.POST)
        if ispindel_coefficient_form.is_valid():
            sensor.ispindel_configuration.third_degree_coefficient = ispindel_coefficient_form.cleaned_data['a']
            sensor.ispindel_configuration.second_degree_coefficient = ispindel_coefficient_form.cleaned_data['b']
            sensor.ispindel_configuration.first_degree_coefficient = ispindel_coefficient_form.cleaned_data['c']
            sensor.ispindel_configuration.constant_term = ispindel_coefficient_form.cleaned_data['d']

            if sensor.ispindel_configuration.coefficients_up_to_date:
                # If we are manually setting the coefficients, then we'll assume they're up to date
                sensor.ispindel_configuration.coefficients_up_to_date = True

            sensor.ispindel_configuration.save()
            messages.success(request, u"Coefficients updated")

        else:
            messages.error(request, u"Invalid coefficients provided")
    else:
        messages.error(request, u"No coefficients provided")

    return redirect("gravity_manage", sensor_id=sensor_id)


@login_required
@site_is_configured
def gravity_ispindel_add_calibration_point(request, sensor_id):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.edit_device'):
    #     messages.error(request, 'Your account is not permissioned to edit devices. Please contact an admin')
    #     return redirect("/")

    try:
        sensor = GravitySensor.objects.get(id=sensor_id)
    except:
        messages.error(request, u'Unable to load sensor with ID {}'.format(sensor_id))
        return redirect('gravity_log_list')

    if sensor.sensor_type != GravitySensor.SENSOR_ISPINDEL:
        messages.error(request, u'Sensor {} is not an iSpindel and cannot be configured in this way!'.format(sensor_id))
        return redirect('gravity_log_list')

    if request.POST:
        ispindel_calibration_point_form = forms.IspindelCalibrationPointForm(request.POST)
        if ispindel_calibration_point_form.is_valid():

            messages.success(request, u"Calibration point added")

            if sensor.ispindel_configuration.coefficients_up_to_date:
                # If we're changing any coefficients since the calibration script was last run, clear the 'calibrated'
                # flag so we know.
                messages.warning(request, u"New calibration points have been added since the coefficients were last"
                                          u"calculated - please re-run the coefficient calculation script to update"
                                          u"the specific gravity equation.")
                sensor.ispindel_configuration.coefficients_up_to_date = False
                sensor.save()

        else:
            messages.error(request, u"Invalid calibration point provided")
    else:
        messages.error(request, u"No calibration point provided")

    return redirect("gravity_manage", sensor_id=sensor_id)


@login_required
@site_is_configured
def gravity_ispindel_delete_calibration_point(request, sensor_id, point_id):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.edit_device'):
    #     messages.error(request, 'Your account is not permissioned to edit devices. Please contact an admin')
    #     return redirect("/")

    try:
        sensor = GravitySensor.objects.get(id=sensor_id)
    except:
        messages.error(request, u'Unable to load sensor with ID {}'.format(sensor_id))
        return redirect('gravity_log_list')

    if sensor.sensor_type != GravitySensor.SENSOR_ISPINDEL:
        messages.error(request, u'Sensor {} is not an iSpindel and cannot be configured in this way!'.format(sensor_id))
        return redirect('gravity_log_list')

    try:
        point = IspindelGravityCalibrationPoint.objects.get(id=point_id)
    except:
        messages.error(request, u'Unable to find calibration point with ID {}!'.format(point_id))
        return redirect("gravity_manage", sensor_id=sensor_id)

    if point.sensor != sensor.ispindel_configuration:
        messages.error(request, u"Point {} doesn't belong to sensor {}!".format(point_id, sensor_id))
        return redirect("gravity_manage", sensor_id=sensor_id)

    # The sensor exists & is an ispindel, the point exists & belongs to the sensor. Delete it.
    point.delete()

    messages.success(request, u"Calibration point removed")

    if sensor.ispindel_configuration.coefficients_up_to_date:
        # If we're changing any coefficients since the calibration script was last run, clear the 'calibrated'
        # flag so we know.
        messages.warning(request, u"Calibration points have been removed since the coefficients were last"
                                  u"calculated - please re-run the coefficient calculation script to update"
                                  u"the specific gravity equation.")
        sensor.ispindel_configuration.coefficients_up_to_date = False
        sensor.save()

    return redirect("gravity_manage", sensor_id=sensor_id)
