import logging
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from app.models import BrewPiDevice
from lib.ftcircus.client import CircusException

logger = logging.getLogger(__name__)

def _JsonResponseIndent(request):
    """Simple function that returns JsonResponse with indent 4"""
    return JsonResponse(request, json_dumps_params={'indent': 4})

@login_required
def stop_brewpi_device(request, device_id):
    """Stop Brewpi Process, like suspend, it is still in cirucs but stopped.
    Returns:
        Error: {'status': 'error', message: 'description'}
        OK:    {'status': 'ok', message: 'description'}
    """
    try:
        active_device = BrewPiDevice.objects.get(id=device_id)
    except:
        logger.error("Error loading device with ID: {}".format(device_id), exc_info=True)
        ret = {'status': 'error', 'message': 'Unable to load device id: {}'.format(device_id)}
        return _JsonResponseIndent(ret)
    try:
        active_device.stop_process()
    except (CircusException) as cerror:
        logger.error("Error during circus call", exc_info=True)
        ret = {'status': 'error', 'message': 'Error during circus call: {}'.format(cerror)}
        return _JsonResponseIndent(ret)
    ret = {'status': 'ok', 'message': 'process signaled to be stopped'}
    return _JsonResponseIndent(ret)

@login_required
def start_brewpi_device(request, device_id):
    """Start Brewpi Process, there must exist an stopped process.
    Returns:
        Error: {'status': 'error', message: 'description'}
        OK:    {'status': 'ok', message: 'description'}
    """
    try:
        active_device = BrewPiDevice.objects.get(id=device_id)
    except:
        logger.error("Error loading device with ID: {}".format(device_id), exc_info=True)
        ret = {'status': 'error', 'message': 'Unable to load device id: {}'.format(device_id)}
        return _JsonResponseIndent(ret)
    try:
        active_device.start_process()
    except (CircusException) as cerror:
        logger.error("Error during circus call", exc_info=True)
        ret = {'status': 'error', 'message': 'Error during circus call: {}'.format(cerror)}
        return _JsonResponseIndent(ret)
    ret = {'status': 'ok', 'message': 'process signaled to start'}
    return _JsonResponseIndent(ret)

@login_required
def status_brewpi_device(request, device_id):
    """Get status of Brewpi Process
    Returns:
        Error: {'status': 'error', message: 'description'}
        OK:    {'status': 'ok', message: '<status>'}
        Where <status> can be: stopped,active,not running
    """
    try:
        active_device = BrewPiDevice.objects.get(id=device_id)
    except:
        logger.error("Error loading device with ID: {}".format(device_id), exc_info=True)
        ret = {'status': 'error', 'message': 'Unable to load device id: {}'.format(device_id)}
        return _JsonResponseIndent(ret)
    try:
        status = active_device.status_process()
    except (CircusException) as cerror:
        logger.error("Error during circus call", exc_info=True)
        ret = {'status': 'error', 'message': 'Error during circus call: {}'.format(cerror)}
        return _JsonResponseIndent(ret)
    ret = {'status': 'ok', 'message': status}
    return _JsonResponseIndent(ret)

@login_required
def remove_brewpi_device(request, device_id):
    """Remove (and stop) Brewpi Process
    Returns:
        Error: {'status': 'error', message: 'description'}
        OK:    {'status': 'ok', message: 'removed'}
    """
    try:
        active_device = BrewPiDevice.objects.get(id=device_id)
    except:
        logger.error("Error loading device with ID: {}".format(device_id), exc_info=True)
        ret = {'status': 'error', 'message': 'Unable remove device id: {}'.format(device_id)}
        return _JsonResponseIndent(ret)
    try:
        active_device.remove_process()
    except (CircusException) as cerror:
        logger.error("Error during circus call", exc_info=True)
        ret = {'status': 'error', 'message': 'Error during circus call: {}'.format(cerror)}
        return _JsonResponseIndent(ret)
    ret = {'status': 'ok', 'message': "removed"}
    return _JsonResponseIndent(ret)
