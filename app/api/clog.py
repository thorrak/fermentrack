import string
import os
from django.http import HttpResponse
from django.conf import settings
from app.models import BrewPiDevice
from django.contrib import messages


def brewpi_spawner_log(req, lines=100):
    logfile_path = os.path.join(settings.BASE_DIR, 'log', 'fermentrack-brewpi-spawner.log')
    try:
        logfile_fd = open(logfile_path)
        ret = tail(logfile_fd, int(lines))
        logfile_fd.close()
    except (IOError) as e:
        return HttpResponse("Error opening logfile: {}".format(str(e)), status=500)
    return HttpResponse(ret, content_type="text/plain")


def fermentrack_log(req, lines=100):
    logfile_path = os.path.join(settings.BASE_DIR, 'log', 'fermentrack-stderr.log')
    try:
        logfile_fd = open(logfile_path)
        ret = tail(logfile_fd, int(lines))
        logfile_fd.close()
    except (IOError) as e:
        return HttpResponse("Error opening logfile {}".format(str(e)), status=500)
    return HttpResponse(ret, content_type="text/plain")


def get_device_log_plain(req, logfile, device_id, lines=100):
    """Read the log files created by circus for spawned controllers"""
    try:
        device = BrewPiDevice.objects.get(id=device_id)
    except:
        # Unable to load the device
        return HttpResponse("No brewpi device with id {}".format(device_id), status=500)

    logfile_path = os.path.join(
        settings.BASE_DIR,
        'log',
        'dev-{}-{}.log'.format(
            device.device_name.lower(),
            logfile)
        )

    try:
        logfile_fd = open(logfile_path)
        ret = tail(logfile_fd, int(lines))
        logfile_fd.close()
    except (IOError) as e:
        # Generally if we hit this the log file doesn't exist
        return HttpResponse("Error opening {} logfile: {}".format(logfile, str(e)), status=500)
    return HttpResponse(ret, content_type="text/plain")


def get_stdout_as_json(req, device_id, lines=100):
    """The stdout log file has json data, we try to split it out and
    only return the raw json data.
    """
    try:
        device = BrewPiDevice.objects.get(id=device_id)
    except:
        # Unable to load the device
        return HttpResponse("No brewpi device with id {}".format(device_id), status=500)

    stdout_log = os.path.join(
        settings.BASE_DIR,
        'log',
        'dev-{}-stdout.log'.format(
            device.device_name.lower())
        )

    try:
        stdout_fd = open(stdout_log)
        ret = tail(stdout_fd, int(lines))
        stdout_fd.close()
    except (IOError) as e:
        # Generally if we hit this the log file doesn't exist
        return HttpResponse("Error opening logfile: {}".format(str(e)), status=500)

    new_ret = []
    # TODO: This is probably too hacky, but only matters if we end up using it :)
    for line in ret:
        new_ret.append("{" + line.split("  {")[1])
    return HttpResponse(new_ret, content_type="application/json")


def tail(f, lines=1, _buffer=4098):
    """Tail a file and get X lines from the end"""
    lines_found = []
    # block counter will be multiplied by buffer
    # to get the block size from the end
    block_counter = -1
    # loop until we find X lines
    while len(lines_found) < lines:
        try:
            f.seek(block_counter * _buffer, os.SEEK_END)
        except IOError:  # either file is too small, or too many lines requested
            f.seek(0)
            lines_found = f.readlines()
            break
        lines_found = f.readlines()
        # we found enough lines, get out
        if len(lines_found) > lines:
            break
        # decrement the block counter to get the
        # next X bytes
        block_counter -= 1
    return lines_found[-lines:]
