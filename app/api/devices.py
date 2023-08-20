from django.http import JsonResponse
from django.urls import reverse
from constance import config

from app.models import BrewPiDevice


def get_devices(req):
    active_devices = list(BrewPiDevice.objects.filter(status=BrewPiDevice.STATUS_ACTIVE).values_list('id', flat=True))
    return JsonResponse(active_devices, safe=False, json_dumps_params={'indent': 4})

