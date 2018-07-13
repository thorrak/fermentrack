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

from gravity.models import GravitySensor, GravityLog, IspindelConfiguration, GravityLogPoint, TiltGravityCalibrationPoint
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
def gravity_tilt_coefficients(request, sensor_id):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.edit_device'):
    #     messages.error(request, 'Your account is not permissioned to edit devices. Please contact an admin')
    #     return redirect("/")

    try:
        sensor = GravitySensor.objects.get(id=sensor_id)
    except:
        messages.error(request, u'Unable to load sensor with ID {}'.format(sensor_id))
        return redirect('gravity_log_list')

    if sensor.sensor_type != GravitySensor.SENSOR_TILT:
        messages.error(request, u'Sensor {} is not a Tilt and cannot be configured in this way'.format(sensor_id))
        return redirect('gravity_log_list')

    if request.POST:
        tilt_coefficient_form = forms.TiltCoefficientForm(request.POST)
        if tilt_coefficient_form.is_valid():
            # sensor.tilt_configuration.grav_third_degree_coefficient = tilt_coefficient_form.cleaned_data['a']
            sensor.tilt_configuration.grav_second_degree_coefficient = tilt_coefficient_form.cleaned_data['b']
            sensor.tilt_configuration.grav_first_degree_coefficient = tilt_coefficient_form.cleaned_data['c']
            sensor.tilt_configuration.grav_constant_term = tilt_coefficient_form.cleaned_data['d']

            if sensor.tilt_configuration.coefficients_up_to_date:
                # If we are manually setting the coefficients, then we'll assume they're up to date
                sensor.tilt_configuration.coefficients_up_to_date = True

            sensor.tilt_configuration.save()
            messages.success(request, u"Coefficients updated")

        else:
            messages.error(request, u"Invalid coefficients provided")
    else:
        messages.error(request, u"No coefficients provided")

    return redirect("gravity_manage", sensor_id=sensor_id)


@login_required
@site_is_configured
def gravity_tilt_add_gravity_calibration_point(request, sensor_id):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.edit_device'):
    #     messages.error(request, 'Your account is not permissioned to edit devices. Please contact an admin')
    #     return redirect("/")

    try:
        sensor = GravitySensor.objects.get(id=sensor_id)
    except:
        messages.error(request, u'Unable to load sensor with ID {}'.format(sensor_id))
        return redirect('gravity_log_list')

    if sensor.sensor_type != GravitySensor.SENSOR_TILT:
        messages.error(request, u'Sensor {} is not a Tilt and cannot be configured in this way'.format(sensor_id))
        return redirect('gravity_log_list')

    if request.POST:
        tilt_calibration_point_form = forms.TiltGravityCalibrationPointForm(request.POST)
        if tilt_calibration_point_form.is_valid():
            tilt_calibration_point_form.save()
            messages.success(request, u"Calibration point added")

            if sensor.ispindel_configuration.coefficients_up_to_date:
                # If we're changing any coefficients since the calibration script was last run, clear the 'calibrated'
                # flag so we know.
                messages.warning(request, u"New calibration points have been added since the coefficients were last "
                                          u"calculated - please re-run the coefficient calculation script to update "
                                          u"the specific gravity equation.")
                sensor.tilt_configuration.coefficients_up_to_date = False
                sensor.tilt_configuration.save()

        else:
            messages.error(request, u"Invalid calibration point provided")
    else:
        messages.error(request, u"No calibration point provided")

    return redirect("gravity_manage", sensor_id=sensor_id)



@login_required
@site_is_configured
def gravity_tilt_delete_gravity_calibration_point(request, sensor_id, point_id):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.edit_device'):
    #     messages.error(request, 'Your account is not permissioned to edit devices. Please contact an admin')
    #     return redirect("/")

    try:
        sensor = GravitySensor.objects.get(id=sensor_id)
    except:
        messages.error(request, u'Unable to load sensor with ID {}'.format(sensor_id))
        return redirect('gravity_log_list')

    if sensor.sensor_type != GravitySensor.SENSOR_TILT:
        messages.error(request, u'Sensor {} is not a Tilt and cannot be configured in this way'.format(sensor_id))
        return redirect('gravity_log_list')

    try:
        point = TiltGravityCalibrationPoint.objects.get(id=point_id)
    except:
        messages.error(request, u'Unable to find calibration point with ID {}'.format(point_id))
        return redirect("gravity_manage", sensor_id=sensor_id)

    if point.sensor != sensor.tilt_configuration:
        messages.error(request, u"Point {} doesn't belong to sensor {}".format(point_id, sensor_id))
        return redirect("gravity_manage", sensor_id=sensor_id)

    # The sensor exists & is a Tilt, the point exists & belongs to the sensor. Delete it.
    point.delete()

    messages.success(request, u"Calibration point removed")

    if sensor.tilt_configuration.coefficients_up_to_date:
        # If we're changing any coefficients since the calibration script was last run, clear the 'calibrated'
        # flag so we know.
        messages.warning(request, u"Calibration points have been removed since the coefficients were last "
                                  u"calculated - please re-run the coefficient calculation script to update "
                                  u"the specific gravity equation.")
        sensor.tilt_configuration.coefficients_up_to_date = False
        sensor.tilt_configuration.save()

    return redirect("gravity_manage", sensor_id=sensor_id)


@login_required
@site_is_configured
def gravity_tilt_calibrate(request, sensor_id):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.edit_device'):
    #     messages.error(request, 'Your account is not permissioned to edit devices. Please contact an admin')
    #     return redirect("/")

    try:
        sensor = GravitySensor.objects.get(id=sensor_id)
    except:
        messages.error(request, u'Unable to load sensor with ID {}'.format(sensor_id))
        return redirect('gravity_log_list')

    if sensor.sensor_type != GravitySensor.SENSOR_TILT:
        messages.error(request, u'Sensor {} is not a Tilt and cannot be configured in this way'.format(sensor_id))
        return redirect('gravity_log_list')

    if not NUMPY_ENABLED:
        messages.error(request, u'The "numpy" python package is not available which is required for calibration')
        return redirect('gravity_log_list')

    points = TiltGravityCalibrationPoint.objects.filter(sensor=sensor.tilt_configuration)


    # Before we do the polyfit, we need to determine the degree of the equation we want to end up with. It doesn't make
    # sense to do a cubic fit with less than 4 points, a quadratic fit less than 3, linear with less than 2, etc. so
    # determine the maximum degrees here (as num points - 1). Max out at quadratic.
    if points.count() < 2:
        messages.error(request, u"Coefficient calculation requires at least 2 (preferably 3+) points to function")
        return redirect("gravity_manage", sensor_id=sensor_id)
    elif points.count() >= 3:
        # If we have more than 4 points, max out at a cubic function
        degree = 2
    else:
        # If we have 2 or 3 points, do a first or second order polyfit
        degree = points.count() - 1

    # For the Tilt, we're not going to complain about a linear fit
    # if degree == 1:
    #     # Although we can do a linear fit, it's not really a good idea. Let the user know what they're getting into.
    #     messages.warning(request, u"Only 2 calibration points available. Your resulting function will be linear, and "
    #                               u"will likely not be accurate. It is highly recommended to add additional points and "
    #                               u"re-perform calibration.")

    # Now set up the x/y arrays and have numpy do the heavy lifting
    x = [float(point.angle) for point in points]
    y = [float(point.gravity) for point in points]
    poly_terms = numpy.polyfit(x, y, degree)

    # Save the results out to our Tilt configuration...
    i = 0  # This is a bit hackish, but it works
    # if degree == 3:
    #     sensor.tilt_configuration.third_degree_coefficient = poly_terms[i]
    #     i += 1
    if degree >= 2:
        sensor.tilt_configuration.grav_second_degree_coefficient = poly_terms[i]
        i += 1
    if degree >= 1:
        sensor.tilt_configuration.grav_first_degree_coefficient = poly_terms[i]
        i += 1
    sensor.tilt_configuration.grav_constant_term = poly_terms[i]

    sensor.tilt_configuration.coefficients_up_to_date = True
    sensor.tilt_configuration.save()

    # ...and we're done!
    messages.success(request, u"Coefficients have been updated based on the calibration points")

    return redirect("gravity_manage", sensor_id=sensor_id)


@login_required
@site_is_configured
def gravity_tilt_guided_calibration(request, sensor_id, step):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.edit_device'):
    #     messages.error(request, 'Your account is not permissioned to edit devices. Please contact an admin')
    #     return redirect("/")

    try:
        sensor = GravitySensor.objects.get(id=sensor_id)
    except:
        messages.error(request, u'Unable to load sensor with ID {}'.format(sensor_id))
        return redirect('gravity_log_list')

    if sensor.sensor_type != GravitySensor.SENSOR_TILT:
        messages.error(request, u"Sensor {} is not a Tilt Hydrometer".format(sensor.name))
        return redirect('gravity_log_list')

    # Let's coerce step to an integer so we can do math on it
    step = int(step)

    # Before we do anything, see if we were passed data. If we were, process it.
    if "sensor" in request.POST:
        tilt_calibration_point_form = forms.TiltGravityCalibrationPointForm(request.POST)
        if tilt_calibration_point_form.is_valid():
            try:
                # If a point exists with the exact same expected specific gravity that we just entered, delete it.
                # This is specifically to prevent the user from accidentally running this calibration twice.
                point_to_delete = TiltGravityCalibrationPoint.objects.get(orig_value=tilt_calibration_point_form.cleaned_data['orig_value'],
                                                                          sensor=sensor.tilt_configuration)
                point_to_delete.delete()
            except:
                # No point existed. We're good.
                pass

            tilt_calibration_point_form.save()
            messages.success(request, u"Calibration point added")

            if sensor.tilt_configuration.coefficients_up_to_date:
                sensor.tilt_configuration.coefficients_up_to_date = False
                sensor.tilt_configuration.save()

        else:
            messages.error(request, u"Invalid calibration point provided - recheck the form try again")
            return redirect("gravity_tilt_guided_calibration", sensor_id=sensor_id, step=(step-1))
    else:
        # If we hit this, the user isn't submitting data. The user is allowed to skip steps - it just isn't recommended.
        pass

    # Alrighty. Let's calculate where we should land on each step of the calibration.

    # Water additions by step & sugar additions by step are both the amount of water/sugar being added in each step
    # in grams.
    water_additions_by_step = [2750, 250, 250, 250, 250, 500]
    sugar_additions_by_step = [0,    300, 300, 300, 300, 600]

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
            point_with_grav = TiltGravityCalibrationPoint.objects.get(gravity=this_step['specific_gravity'],
                                                                      sensor=sensor.tilt_configuration)
            this_step['tilt_gravity'] = point_with_grav.orig_value
        except:
            this_step['tilt_gravity'] = ""

        step_data.append(this_step)

    # Now we're ready to proceed. Let's build the context & then determine what template to output to the user
    context = {'all_steps_data': step_data, 'on_step': step, 'next_step': step+1, 'active_device': sensor}

    if step == 0:
        # Step 0 just lays out the basic instructions. We do want to collect existing points (if any) so we can warn
        # the user, however.
        existing_points = TiltGravityCalibrationPoint.objects.filter(sensor=sensor.ispindel_configuration)
        context['existing_points'] = existing_points
        return render(request, template_name='gravity/gravity_tilt_calibrate_start.html', context=context)
    elif step <= len(water_additions_by_step):
        tilt_calibration_point_form = forms.IspindelCalibrationPointForm(
            initial={'sensor': sensor.tilt_configuration, 'actual_value': step_data[step-1]['specific_gravity']})
        context['tilt_calibration_point_form'] = tilt_calibration_point_form
        context['this_step_data'] = step_data[step - 1]
        return render(request, template_name='gravity/gravity_tilt_calibrate_step.html', context=context)
    else:
        # Last step is just a message.
        return render(request, template_name='gravity/gravity_tilt_calibrate_end.html', context=context)
