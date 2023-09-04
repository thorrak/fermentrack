from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.urls import reverse
from constance import config
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
import json
from ..models import BeerLogPoint, BrewPiDevice
from django.utils import timezone

from app.models import BrewPiDevice


def get_devices(req):
    active_devices = list(BrewPiDevice.objects.filter(status=BrewPiDevice.STATUS_ACTIVE).values_list('id', flat=True))
    return JsonResponse(active_devices, safe=False, json_dumps_params={'indent': 4})


# def get_device(req, device_id):
#     brewpi_device = BrewPiDevice.objects.get(id=device_id)
#
#     device_repr = {
#         'id': brewpi_device.id,
#         'device_name': brewpi_device.device_name,
#         'temp_format': brewpi_device.temp_format,  # Need this one
#         'data_point_log_interval': brewpi_device.data_point_log_interval,
#         'useInetSocket': brewpi_device.useInetSocket,
#         'socketPort': brewpi_device.socketPort,
#         'socketHost': brewpi_device.socketHost,
#         'logging_status': brewpi_device.logging_status,
#         'serial_port': brewpi_device.serial_port,
#         'serial_alt_port': brewpi_device.serial_alt_port,
#         'udev_serial_number': brewpi_device.udev_serial_number,
#         'prefer_connecting_via_udev': brewpi_device.prefer_connecting_via_udev,
#         'board_type': brewpi_device.board_type,
#         'status': brewpi_device.status,
#         'socket_name': brewpi_device.socket_name,
#         'connection_type': brewpi_device.connection_type,
#         'wifi_host': brewpi_device.wifi_host,
#         'wifi_host_ip': brewpi_device.wifi_host_ip,
#         'wifi_port': brewpi_device.wifi_port,
#         'active_beer': brewpi_device.active_beer,  # Need this one
#         'active_profile': brewpi_device.active_profile,
#         'time_profile_started': brewpi_device.time_profile_started,
#         'uuid': brewpi_device.uuid,
#     }
#
#     return JsonResponse(brewpi_device, safe=False, json_dumps_params={'indent': 4})

@csrf_exempt  # We exempt CSRF protection for demonstration purposes. In a real-world scenario, handle this carefully.
def create_beer_log_point(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            brewpi_device = BrewPiDevice.objects.get(id=data.get('brewpi_device_id'))

            beer_log_point = BeerLogPoint(
                beer_temp = data.get('beer_temp'),
                beer_set = data.get('beer_set'),
                beer_ann = data.get('beer_ann'),
                fridge_temp = data.get('fridge_temp'),
                fridge_set = data.get('fridge_set'),
                fridge_ann = data.get('fridge_ann'),
                room_temp = data.get('room_temp'),
                state = data.get('state'),
                temp_format = brewpi_device.temp_format,
                associated_beer = brewpi_device.active_beer,
            )

            beer_log_point.enrich_gravity_data()

            beer_log_point.save()

            return JsonResponse({'status': 'success'}, status=201)
        except ObjectDoesNotExist:
            return JsonResponse({'status': 'device not found'}, status=404)
        except Exception as e:
            return HttpResponseBadRequest(str(e))
    else:
        return JsonResponse({'status': 'method not allowed'}, status=405)
