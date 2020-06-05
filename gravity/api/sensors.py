from django.shortcuts import render
from django.shortcuts import redirect
from django.http import JsonResponse
from django.urls import reverse
from django.core.exceptions import ObjectDoesNotExist
from constance import config

from gravity.models import GravitySensor


def getGravitySensors(req, device_id=None):
    ret = []
    if device_id is None:
        devices = GravitySensor.objects.all()
    else:
        try:
            devices = [GravitySensor.objects.get(id=device_id),]
        except ObjectDoesNotExist:
            devices = []
    for dev in devices:
        if dev.sensor_type == GravitySensor.SENSOR_MANUAL:
            # For manual sensors, we want the "manage device" link to be for adding a reading instead
            manage_text = "Add Reading"
            manage_url = reverse('gravity_add_point', kwargs={'manual_sensor_id': dev.id,})
        else:
            manage_text = "Manage Device"
            manage_url = reverse('gravity_dashboard', kwargs={'sensor_id': dev.id,})

        temp, temp_format = dev.retrieve_loggable_temp()
        if temp is None:
            temp_string = "--.-&deg;"
        else:
            temp_string = "{}&deg; {}".format(temp, temp_format)

        gravity = dev.retrieve_loggable_gravity()
        if gravity is None:
            grav_string = "-.---"
        else:
            grav_string = "{:05.3f}".format(gravity)

        bound_device = {}
        if dev.assigned_brewpi_device is not None:
            bound_device['id'] = dev.assigned_brewpi_device_id
            bound_device['name'] = dev.assigned_brewpi_device.device_name

        ret.append({"device_name": dev.name, "current_gravity": grav_string,
                    "current_temp": temp, "temp_format": temp_format, "temp_string": temp_string,
                    'device_url': reverse('gravity_dashboard', kwargs={'sensor_id': dev.id,}),
                    'manage_text': manage_text, 'manage_url': manage_url,
                    'bound_device': bound_device,
                    'modal_name': '#gravSensor{}'.format(dev.id)})
    return JsonResponse(ret, safe=False, json_dumps_params={'indent': 4})


def get_ispindel_extras(req, device_id):
    try:
        device = GravitySensor.objects.get(id=device_id)
    except ObjectDoesNotExist:
        return JsonResponse({'error': 'Unable to locate device with ID {}'.format(device_id)}, safe=False)

    if device.sensor_type == GravitySensor.SENSOR_ISPINDEL:
        # Load the iSpindel 'extras' from redis
        extras = device.ispindel_configuration.load_extras_from_redis()
        extras['device_name'] = device.name
        extras['device_id'] = device.id
    else:
        extras = {}

    return JsonResponse(extras, safe=False, json_dumps_params={'indent': 4})


def get_tilt_extras(req, device_id):
    try:
        device = GravitySensor.objects.get(id=device_id)
    except ObjectDoesNotExist:
        return JsonResponse({'error': 'Unable to locate device with ID {}'.format(device_id)}, safe=False)

    if device.sensor_type == GravitySensor.SENSOR_TILT:
        # Load the Tilt 'extras' from redis
        extras = device.tilt_configuration.load_extras_from_redis()
        extras['device_name'] = device.name
        extras['device_id'] = device.id
    else:
        extras = {}

    return JsonResponse(extras, safe=False, json_dumps_params={'indent': 4})
