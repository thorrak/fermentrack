import string
import os
from django.http import HttpResponse
from django.conf import settings
from app.models import BrewPiDevice

def get_device_log_plain(req, logfile, device_id, lines=100):
    """Read the log files created by circus for spawned controllers"""
    device = BrewPiDevice.objects.get(id=device_id)
    logfile = string.join([
        settings.BASE_DIR,
        '/log/dev-',
        device.device_name,
        '-',
        logfile,
        '.log'], '')
    logfile_fd = open(logfile)
    ret = tail(logfile_fd, int(lines))
    logfile_fd.close()
    return HttpResponse(ret, content_type="text/plain")

def get_stdout_as_json(req, device_id, lines=100):
    """The stdout log file has json data, we try to split it out and
    only return the raw json data.
    """
    device = BrewPiDevice.objects.get(id=device_id)
    stdout_log = string.join([
        settings.BASE_DIR,
        '/log/dev-',
        device.device_name,
        '-stdout.log'], '')
    stdout_fd = open(stdout_log)
    ret = tail(stdout_fd, int(lines))
    stdout_fd.close()
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
