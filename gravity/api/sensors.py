from django.shortcuts import render
from django.contrib import messages
from django.shortcuts import render_to_response, redirect
from django.http import JsonResponse
from django.urls import reverse
from constance import config

from gravity.models import GravitySensor


def getGravitySensors(req, device_id=None):
    ret = []
    if device_id is None:
        devices = GravitySensor.objects.all()
    else:
        devices = GravitySensor.objects.get(id=device_id)
    for dev in devices:
        if dev.sensor_type == GravitySensor.SENSOR_MANUAL:
            # For manual sensors, we want the "manage device" link to be for adding a reading instead
            manage_text = "Add Reading"
            manage_url = reverse('gravity_add_point', kwargs={'manual_sensor_id': dev.id,})
        else:
            manage_text = "Manage Device"
            manage_url = reverse('gravity_dashboard', kwargs={'sensor_id': dev.id,})

        temp, temp_format = dev.retrieve_latest_temp()

        ret.append({"device_name": dev.name, "current_gravity": dev.retrieve_latest_gravity(),
                    "current_temp": temp, "temp_format": temp_format,
                    'device_url': reverse('gravity_dashboard', kwargs={'sensor_id': dev.id,}),
                    'manage_text': manage_text, 'manage_url': manage_url,
                    'modal_name': '#gravSensor{}'.format(dev.id)})
    return JsonResponse(ret, safe=False, json_dumps_params={'indent': 4})

#
#
# def getPanel(req, device_id):
#
#     # Don't repeat yourself...
#     def temp_text(temp, temp_format):
#         if temp == 0:
#             return "--&deg; {}".format(temp_format)
#         else:
#             return "{}&deg; {}".format(temp, temp_format)
#
#     ret = []
#     try:
#         dev = BrewPiDevice.objects.get(id=device_id)
#         device_info = dev.get_dashpanel_info()
#     except:
#         # We were given an invalid panel number - Just send back the equivalent of null data
#         null_temp = temp_text(0, config.TEMPERATURE_FORMAT)
#         ret.append({'beer_temp': null_temp, 'fridge_temp': null_temp, 'room_temp': null_temp, 'control_mode': "--",
#                     'log_interval': 0})
#         return JsonResponse(ret, safe=False, json_dumps_params={'indent': 4})
#
#
#     if device_info['Mode'] == "o":
#         device_mode = "Off"
#     elif device_info['Mode'] == "f":
#         device_mode = "Fridge Constant"
#     elif device_info['Mode'] == "b":
#         device_mode = "Beer Constant"
#     elif device_info['Mode'] == "p":
#         device_mode = "Beer Profile"
#     else:
#         # TODO - Log This
#         device_mode = "--"
#
#     if int(device_info['LogInterval']) <= 90:
#         interval_text = "{} seconds".format(int(device_info['LogInterval']))
#     elif int(device_info['LogInterval']) < (60*60):
#         interval_text = "{} minutes".format(int(device_info['LogInterval']/60))
#     else:
#         interval_text = "{} hour".format(int(device_info['LogInterval']/(60*60)))
#         if int(device_info['LogInterval']) >= (60*60*2):
#             interval_text += "s"  # IT WORKS. QUIT JUDGING.
#
#
#     ret.append({'beer_temp': temp_text(device_info['BeerTemp'], dev.temp_format),
#                 'fridge_temp': temp_text(device_info['FridgeTemp'], dev.temp_format),
#                 'room_temp': temp_text(device_info['RoomTemp'], dev.temp_format),
#                 'control_mode': device_mode,
#                 'log_interval': interval_text})
#
#     return JsonResponse(ret, safe=False, json_dumps_params={'indent': 4})
