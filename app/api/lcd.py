from django.shortcuts import render
from django.contrib import messages
from django.shortcuts import render_to_response, redirect
from django.http import JsonResponse
from django.urls import reverse

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

# TODO - Implement this
def getPanel(req, device_id):
    ret = []

    ret.append({'beer_temp': "64&deg; F", 'fridge_temp': "65&deg; F", 'control_mode': "Beer Profile", 'log_interval': 30
                })

    return JsonResponse(ret, safe=False, json_dumps_params={'indent': 4})
