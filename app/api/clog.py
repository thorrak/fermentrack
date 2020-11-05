import os
from django.http import HttpResponse
from django.conf import settings
from app.models import BrewPiDevice
from gravity.models import GravitySensor


def get_filepath_to_log(device_type, logfile="", device_id=None):
    # get_filepath_to_log is being broken out so that we can use it in help/other templates to display which log file
    # is being loaded
    if device_type == "brewpi":
        try:
            device = BrewPiDevice.objects.get(id=device_id)
            log_filename = 'dev-{}-{}.log'.format(str(device.circus_parameter()).lower(), logfile)
        except:
            # Unable to load the device
            raise ValueError("No brewpi device with id {}".format(device_id))

    elif device_type == "spawner":
        log_filename = 'fermentrack-processmgr.log'
    elif device_type == "fermentrack":
        log_filename = 'fermentrack-stderr.log'
    elif device_type == "ispindel":
        log_filename = 'ispindel_raw_output.log'
    elif device_type == "upgrade":
        log_filename = 'upgrade.log'
    else:
        return None

    # Once we've determined the filename from logfile and device_type, let's open it up & read it in
    logfile_path = os.path.join(settings.BASE_DIR, 'log', log_filename)
    return logfile_path


def get_device_log_combined(req, return_type, device_type, logfile, device_id=None, lines=100):
    """Read the log files created by circus for spawned controllers"""

    # TODO - THIS IS A HACK. This needs to be fixed properly, but that will require some refactoring
    if(device_type=="upgrade"):
        lines = 1000

    # Although the urlpattern checks if the logfile type is valid, this gets used in the filename we're reading so
    # recheck it here just to be safe.
    valid_logfile_types = ['stdout', 'stderr']
    if logfile not in valid_logfile_types:
        return HttpResponse("File type {} not a valid log file to read".format(device_id), status=500)

    # Device_type determines the other part of the logfile to read. Valid options are:
    # brewpi - A BrewPiDevice object
    # gravity - A specific gravity sensor object
    # spawner - the circus spawner
    # fermentrack - Fermentrack itself
    valid_device_types = ['brewpi', 'gravity', 'spawner', 'fermentrack', 'ispindel', 'upgrade']
    if device_type not in valid_device_types:
        # TODO - Log this
        return HttpResponse("Cannot read log files for devices of type {} ".format(device_type), status=500)

    # Load the full path to the logfile, then open it and load the file itself
    logfile_path = get_filepath_to_log(device_type, logfile, device_id)

    try:
        logfile_fd = open(logfile_path)
        ret = tail(logfile_fd, int(lines))
        logfile_fd.close()
    except (IOError) as e:
        # Generally if we hit this the log file doesn't exist
        return HttpResponse("Error opening {} logfile: {}".format(logfile_path, str(e)), status=500)

    # Now that we have the log loaded, format the output to match what the user wants (either text or json)
    if return_type == "text":
        return HttpResponse(ret, content_type="text/plain")
    elif return_type == "json":
        new_ret = []
        # TODO: This is probably too hacky, but only matters if we end up using it :)
        for line in ret:
            new_ret.append("{" + line.split("  {")[1])
        return HttpResponse(new_ret, content_type="application/json")
    else:
        return HttpResponse("Invalid log output type: {} ".format(return_type), status=500)


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
