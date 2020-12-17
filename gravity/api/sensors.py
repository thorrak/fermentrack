from django.http import JsonResponse
from django.urls import reverse
from django.core.exceptions import ObjectDoesNotExist
from constance import config
from django.utils import timezone
import datetime

from gravity.models import GravitySensor


def get_gravity_sensors(req, device_id=None):
    ret = []
    if device_id is None:
        devices = GravitySensor.objects.all()
    else:
        try:
            devices = [GravitySensor.objects.get(id=device_id), ]
        except ObjectDoesNotExist:
            devices = []
    for dev in devices:
        if dev.sensor_type == GravitySensor.SENSOR_MANUAL:
            # For manual sensors, we want the "manage device" link to be for adding a reading instead
            manage_text = "Add Reading"
            manage_url = reverse('gravity_add_point', kwargs={'manual_sensor_id': dev.id, })
        else:
            manage_text = "Manage Device"
            manage_url = reverse('gravity_dashboard', kwargs={'sensor_id': dev.id, })

        # To reduce confusion about what is going on with gravity sensor check-ins, if we haven't received a recent
        # check-in, we want this API to act as if no point is available. The point has to remain available, though,
        # in order to be used for logging (so graphs don't look wonky)
        if dev.sensor_type == GravitySensor.SENSOR_TILT:
            point_expiry = datetime.timedelta(minutes=2)  # Tilts report in roughly every second. This should be plenty.
        elif dev.sensor_type == GravitySensor.SENSOR_ISPINDEL:
            point_expiry = datetime.timedelta(minutes=62)  # iSpindels sleep for a long time. Giving them over an hour.
        else:
            point_expiry = datetime.timedelta(days=30)  # For all other sensors (including manual) extend this way out

        log_point = dev.retrieve_latest_point()
        if log_point is None:
            temp = None
            gravity = None
        elif log_point.log_time < timezone.now() - point_expiry:
            # If the last log point was received too long ago, act like we don't have a point to display
            temp = None
            gravity = None
        else:
            temp, temp_format = dev.retrieve_loggable_temp()
            gravity = dev.retrieve_loggable_gravity()

        if temp is None:
            temp_string = "--.-&deg;"
        else:
            temp_string = f"{temp}&deg; {temp_format}"

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
        extras['log_time'] = device.ispindel_configuration.load_last_log_time_from_redis()
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
