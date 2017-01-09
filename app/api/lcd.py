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
                    'device_url': reverse('device_dashboard', kwargs={'device_id': dev.id,})})
    return JsonResponse(ret, safe=False, json_dumps_params={'indent': 4})

def getLCD(req, device_name):
    device = BrewPiDevice.objects.get(device_name=device_name)
    return JsonResponse(device.read_lcd(), safe=False, json_dumps_params={'indent': 4})