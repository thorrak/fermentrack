from django.shortcuts import render
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth import login
from django.contrib.auth.models import User
from constance import config
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json, socket, decimal
from django.http import JsonResponse

from gravity.models import GravitySensor, GravityLog, IspindelConfiguration, GravityLogPoint, IspindelGravityCalibrationPoint
try:
    import numpy
    NUMPY_ENABLED = True
except:
    NUMPY_ENABLED = False


from app.decorators import site_is_configured, login_if_required_for_dashboard, gravity_support_enabled

import os, datetime, pytz, logging

import gravity.forms as forms

logger = logging.getLogger(__name__)

import fermentrack_django.settings as settings


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
        if ":" in fermentrack_host:
            fermentrack_host = fermentrack_host[:fermentrack_host.find(":")]
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
        logger.error("No data in iSpindel request body")
        return JsonResponse({'status': 'failed', 'message': "No data in request body"}, safe=False,
                            json_dumps_params={'indent': 4})

    import pprint
    with open(os.path.join(settings.BASE_DIR, "log", 'ispindel_raw_output.log'), 'w') as logFile:
        pprint.pprint(request.body.decode('utf-8'), logFile)

    # As of the iSpindel firmware version 5.6.1, the json posted contains the following fields:
    # {u'ID': 3003098,
    #  u'angle': 77.4576,
    #  u'battery': 4.171011,
    #  u'gravity': 27.22998,
    #  u'name': u'iSpindel123',
    #  u'temperature': 24.75,
    #  u'token': u'tokengoeshere'}

    # As of iSpindel 6.2.0 it looks like this:
    # {"name":"iSpindel001","ID":9390968,"token":"fermentrack","angle":68.81093,"temperature":73.175,"temp_units":"F","battery":4.103232,"gravity":22.80585,"interval":20,"RSSI":-41}

    try:
        ispindel_data = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return JsonResponse({'status': 'failed', 'message': "No JSON data was posted (are you accessing this manually?)"}, safe=False,
                            json_dumps_params={'indent': 4})

    with open(os.path.join(settings.BASE_DIR, "log", 'ispindel_json_output.log'), 'w') as logFile:
        pprint.pprint(ispindel_data, logFile)

    try:
        ispindel_obj = IspindelConfiguration.objects.get(name_on_device=ispindel_data['name'])
    except:
        logger.error(u"Unable to load sensor with name {}".format(ispindel_data['name']))
        return JsonResponse({'status': 'failed', 'message': "Unable to load sensor with that name"}, safe=False,
                            json_dumps_params={'indent': 4})


    # Let's calculate the gravity using the coefficients stored in the ispindel configuration. This will allow us to
    # reconfigure on the fly.
    angle = float(ispindel_data['angle'])

    calculated_gravity = ispindel_obj.third_degree_coefficient * angle**3
    calculated_gravity += ispindel_obj.second_degree_coefficient * angle**2
    calculated_gravity += ispindel_obj.first_degree_coefficient * angle
    calculated_gravity += ispindel_obj.constant_term

    if 'temp_units' in ispindel_data:
        # If we were provided temp units, use them
        ispindel_temp_units = ispindel_data['temp_units']
    else:
        # Default to celsius
        ispindel_temp_units = 'C'

    converted_temp, temp_format = ispindel_obj.sensor.convert_temp_to_sensor_format(float(ispindel_data['temperature']),
                                                                                    ispindel_temp_units)

    new_point = GravityLogPoint(
        gravity=calculated_gravity,         # We're using the gravity we calc within Fermentrack
        temp=converted_temp,
        temp_format=temp_format,
        temp_is_estimate=False,
        associated_device=ispindel_obj.sensor,
        gravity_latest=calculated_gravity,
        temp_latest=converted_temp,
        extra_data=angle,
    )

    if ispindel_obj.sensor.active_log is not None:
        new_point.associated_log = ispindel_obj.sensor.active_log

    new_point.save()

    # Set & save the 'extra' data points to redis (so we can load & use later)
    ispindel_obj.angle = angle
    if 'ID' in ispindel_data:
        ispindel_obj.ispindel_id = ispindel_data['ID']
    if 'battery' in ispindel_data:
        ispindel_obj.battery = ispindel_data['battery']
    if 'gravity' in ispindel_data:
        ispindel_obj.ispindel_gravity = ispindel_data['gravity']
    if 'token' in ispindel_data:
        ispindel_obj.token = ispindel_data['token']
    ispindel_obj.save_extras_to_redis()

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
        messages.error(request, u'Sensor {} is not an iSpindel and cannot be configured in this way'.format(sensor_id))
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
        messages.error(request, u'Sensor {} is not an iSpindel and cannot be configured in this way'.format(sensor_id))
        return redirect('gravity_log_list')

    if request.POST:
        ispindel_calibration_point_form = forms.IspindelCalibrationPointForm(request.POST)
        if ispindel_calibration_point_form.is_valid():
            ispindel_calibration_point_form.save()
            messages.success(request, u"Calibration point added")

            if sensor.ispindel_configuration.coefficients_up_to_date:
                # If we're changing any coefficients since the calibration script was last run, clear the 'calibrated'
                # flag so we know.
                messages.warning(request, u"New calibration points have been added since the coefficients were last "
                                          u"calculated - please re-run the coefficient calculation script to update "
                                          u"the specific gravity equation.")
                sensor.ispindel_configuration.coefficients_up_to_date = False
                sensor.ispindel_configuration.save()

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
        messages.error(request, u'Sensor {} is not an iSpindel and cannot be configured in this way'.format(sensor_id))
        return redirect('gravity_log_list')

    try:
        point = IspindelGravityCalibrationPoint.objects.get(id=point_id)
    except:
        messages.error(request, u'Unable to find calibration point with ID {}'.format(point_id))
        return redirect("gravity_manage", sensor_id=sensor_id)

    if point.sensor != sensor.ispindel_configuration:
        messages.error(request, u"Point {} doesn't belong to sensor {}".format(point_id, sensor_id))
        return redirect("gravity_manage", sensor_id=sensor_id)

    # The sensor exists & is an ispindel, the point exists & belongs to the sensor. Delete it.
    point.delete()

    messages.success(request, u"Calibration point removed")

    if sensor.ispindel_configuration.coefficients_up_to_date:
        # If we're changing any coefficients since the calibration script was last run, clear the 'calibrated'
        # flag so we know.
        messages.warning(request, u"Calibration points have been removed since the coefficients were last "
                                  u"calculated - please re-run the coefficient calculation script to update "
                                  u"the specific gravity equation.")
        sensor.ispindel_configuration.coefficients_up_to_date = False
        sensor.ispindel_configuration.save()

    return redirect("gravity_manage", sensor_id=sensor_id)


@login_required
@site_is_configured
def gravity_ispindel_calibrate(request, sensor_id):
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
        messages.error(request, u'Sensor {} is not an iSpindel and cannot be configured in this way'.format(sensor_id))
        return redirect('gravity_log_list')

    if not NUMPY_ENABLED:
        messages.error(request, u'The "numpy" python package is not available which is required for calibration')
        return redirect('gravity_log_list')

    points = IspindelGravityCalibrationPoint.objects.filter(sensor=sensor.ispindel_configuration)


    # Before we do the polyfit, we need to determine the degree of the equation we want to end up with. It doesn't make
    # sense to do a cubic fit with less than 4 points, a quadratic fit less than 3, linear with less than 2, etc. so
    # determine the maximum degrees here (as num points - 1). Max out at cubic.
    if points.count() < 2:
        messages.error(request, u"Coefficient calculation requires at least 2 (preferably 3+) points to function")
        return redirect("gravity_manage", sensor_id=sensor_id)
    elif points.count() >= 4:
        # If we have more than 4 points, max out at a cubic function
        degree = 3
    else:
        # If we have 2 or 3 points, do a first or second order polyfit
        degree = points.count() - 1

    if degree == 1:
        # Although we can do a linear fit, it's not really a good idea. Let the user know what they're getting into.
        messages.warning(request, u"Only 2 calibration points available. Your resulting function will be linear, and "
                                  u"will likely not be accurate. It is highly recommended to add additional points and "
                                  u"re-perform calibration.")

    # Now set up the x/y arrays and have numpy do the heavy lifting
    x = [float(point.angle) for point in points]
    y = [float(point.gravity) for point in points]
    poly_terms = numpy.polyfit(x, y, degree)

    # Save the results out to our ispindel configuration...
    i = 0  # This is a bit hackish, but it works
    if degree == 3:
        sensor.ispindel_configuration.third_degree_coefficient = poly_terms[i]
        i += 1
    if degree >= 2:
        sensor.ispindel_configuration.second_degree_coefficient = poly_terms[i]
        i += 1
    if degree >= 1:
        sensor.ispindel_configuration.first_degree_coefficient = poly_terms[i]
        i += 1
    sensor.ispindel_configuration.constant_term = poly_terms[i]

    sensor.ispindel_configuration.coefficients_up_to_date = True
    sensor.ispindel_configuration.save()

    # ...and we're done!
    messages.success(request, u"Coefficients have been updated based on the calibration points")

    return redirect("gravity_manage", sensor_id=sensor_id)


@login_required
@site_is_configured
def gravity_ispindel_guided_calibration(request, sensor_id, step):
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

    # Let's coerce step to an integer so we can do math on it
    step = int(step)

    # Before we do anything, see if we were passed data. If we were, process it.
    if "sensor" in request.POST:
        ispindel_calibration_point_form = forms.IspindelCalibrationPointForm(request.POST)
        if ispindel_calibration_point_form.is_valid():
            try:
                # If a point exists with the exact same specific gravity that we just entered, delete it.
                # This is specifically to prevent the user from accidentally running this calibration twice.
                point_to_delete = IspindelGravityCalibrationPoint.objects.get(gravity=ispindel_calibration_point_form.cleaned_data['gravity'],
                                                                              sensor=sensor.ispindel_configuration)
                point_to_delete.delete()
            except:
                # No point existed. We're good.
                pass

            ispindel_calibration_point_form.save()
            messages.success(request, u"Calibration point added")

            if sensor.ispindel_configuration.coefficients_up_to_date:
                sensor.ispindel_configuration.coefficients_up_to_date = False
                sensor.ispindel_configuration.save()

        else:
            messages.error(request, u"Invalid calibration point provided - recheck the angle you entered & try again")
            return redirect("gravity_ispindel_guided_calibration", sensor_id=sensor_id, step=(step-1))
    else:
        # If we hit this, the user isn't submitting data. The user is allowed to skip steps - it just isn't recommended.
        pass

    # Alrighty. Let's calculate where we should land on each step of the calibration.

    # Water additions by step & sugar additions by step are both the amount of water/sugar being added in each step
    # in grams.
    water_additions_by_step = [2750, 125, 125, 250, 250, 250, 250, 250]
    sugar_additions_by_step = [0,    150, 150, 300, 300, 300, 300, 300]

    # Now let's translate that into data, organized by step (Note - step number is one-off from the 'step' parameter)

    step_data = []
    for i in range(len(water_additions_by_step)):
        this_step = {'step': (i+1)}
        this_step['water_addition'] = water_additions_by_step[i]
        this_step['sugar_addition'] = sugar_additions_by_step[i]

        this_step['cumulative_water'] = this_step['water_addition']
        this_step['cumulative_sugar'] = this_step['sugar_addition']
        if i > 0:
            this_step['cumulative_water'] += step_data[i-1]['cumulative_water']
            this_step['cumulative_sugar'] += step_data[i-1]['cumulative_sugar']

        this_step['plato'] = 1.0*this_step['cumulative_sugar'] / (this_step['cumulative_sugar'] + this_step['cumulative_water']) * 100
        this_step['specific_gravity'] = round(decimal.Decimal(1+this_step['plato']/(258.6-(227.1*(this_step['plato']/258.2)))), 4)
        this_step['plato'] = round(decimal.Decimal(this_step['plato']),2)  # Make it pretty to look at

        try:
            point_with_grav = IspindelGravityCalibrationPoint.objects.get(gravity=this_step['specific_gravity'],
                                                                          sensor=sensor.ispindel_configuration)
            this_step['angle'] = point_with_grav.angle
        except:
            this_step['angle'] = ""

        step_data.append(this_step)

    # Now we're ready to proceed. Let's build the context & then determine what template to output to the user
    context = {'all_steps_data': step_data, 'on_step': step, 'next_step': step+1, 'active_device': sensor}

    if step == 0:
        # Step 0 just lays out the basic instructions. We do want to collect existing points (if any) so we can warn
        # the user, however.
        existing_points = IspindelGravityCalibrationPoint.objects.filter(sensor=sensor.ispindel_configuration)
        context['existing_points'] = existing_points
        return render(request, template_name='gravity/gravity_ispindel_calibrate_start.html', context=context)
    elif step <= len(water_additions_by_step):
        ispindel_calibration_form = forms.IspindelCalibrationPointForm(
            initial={'sensor': sensor.ispindel_configuration, 'gravity': step_data[step-1]['specific_gravity']})
        context['ispindel_calibration_form'] = ispindel_calibration_form
        context['this_step_data'] = step_data[step - 1]
        return render(request, template_name='gravity/gravity_ispindel_calibrate_step.html', context=context)
    else:
        # Last step is just a message.
        return render(request, template_name='gravity/gravity_ispindel_calibrate_end.html', context=context)

