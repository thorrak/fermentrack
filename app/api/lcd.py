from django.shortcuts import render
from django.contrib import messages
from django.shortcuts import render_to_response, redirect
from django.http import JsonResponse
from django.urls import reverse
from constance import config

from app.models import BrewPiDevice


def getLCDs(req):
    ret = []
    all_devices = BrewPiDevice.objects.all()
    for dev in all_devices:
        ret.append({"device_name": dev.device_name, "lcd_data": dev.read_lcd(),
                    'device_url': reverse('device_dashboard', kwargs={'device_id': dev.id,}),
                    'backlight_url': reverse('device_toggle_backlight', kwargs={'device_id': dev.id,}),
                    'modal_name': '#tempControl{}'.format(dev.id)})
    return JsonResponse(ret, safe=False, json_dumps_params={'indent': 4})


def getLCD(req, device_id):
    ret = []
    dev = BrewPiDevice.objects.get(id=device_id)

    ret.append({"device_name": dev.device_name, "lcd_data": dev.read_lcd(),
                'device_url': reverse('device_dashboard', kwargs={'device_id': dev.id, }),
                'backlight_url': reverse('device_toggle_backlight', kwargs={'device_id': dev.id, }),
                'modal_name': '#tempControl{}'.format(dev.id)})

    return JsonResponse(ret, safe=False, json_dumps_params={'indent': 4})


def getPanel(req, device_id):

    # Don't repeat yourself...
    def temp_text(temp, temp_format):
        if temp == 0:
            return "--&deg; {}".format(temp_format)
        else:
            return "{}&deg; {}".format(temp, temp_format)

    ret = []
    try:
        dev = BrewPiDevice.objects.get(id=device_id)
        device_info = dev.get_dashpanel_info()
    except:
        # We were given an invalid panel number - Just send back the equivalent of null data
        null_temp = temp_text(0, config.TEMPERATURE_FORMAT)
        ret.append({'beer_temp': null_temp, 'fridge_temp': null_temp, 'room_temp': null_temp, 'control_mode': "--",
                    'log_interval': 0})
        return JsonResponse(ret, safe=False, json_dumps_params={'indent': 4})


    if device_info['Mode'] == "o":
        device_mode = "Off"
    elif device_info['Mode'] == "f":
        device_mode = "Fridge Constant"
    elif device_info['Mode'] == "b":
        device_mode = "Beer Constant"
    elif device_info['Mode'] == "p":
        device_mode = "Beer Profile"
    else:
        # TODO - Log This
        device_mode = "--"

    if int(device_info['LogInterval']) <= 90:
        interval_text = "{} seconds".format(int(device_info['LogInterval']))
    elif int(device_info['LogInterval']) < (60*60):
        interval_text = "{} minutes".format(int(device_info['LogInterval']/60))
    else:
        interval_text = "{} hour".format(int(device_info['LogInterval']/(60*60)))
        if int(device_info['LogInterval']) >= (60*60*2):
            interval_text += "s"  # IT WORKS. QUIT JUDGING.


    ret.append({'beer_temp': temp_text(device_info['BeerTemp'], dev.temp_format),
                'fridge_temp': temp_text(device_info['FridgeTemp'], dev.temp_format),
                'room_temp': temp_text(device_info['RoomTemp'], dev.temp_format),
                'control_mode': device_mode,
                'log_interval': interval_text})

    return JsonResponse(ret, safe=False, json_dumps_params={'indent': 4})
