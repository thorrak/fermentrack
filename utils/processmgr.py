#!/usr/bin/env python

# This is a process manager used for launching individual instances of BrewPi-script for each valid configuration in
# a Fermentrack database. It is launched & maintained by Circus, and is assumed to itself be daemonized.

# This is the new new version of the BrewPi-script log manager which isn't fully in use.


import os, sys
import time
import logging
import argparse

from circus.util import DEFAULT_ENDPOINT_DEALER
from processmgr_class import ProcessManager

# Load up the Django specific stuff
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# This is so Django knows where to find stuff.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fermentrack_django.settings")
sys.path.append(BASE_DIR)
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
import app.models
import gravity.models


LOG = logging.getLogger("processmgr")
LOG.setLevel(logging.INFO)

# Defaults
SLEEP_INTERVAL = 15


########## BrewPi Script Configuration
BREWPI_SCRIPT_CMD_TEMPLATE = "python -u " + os.path.expanduser("~/fermentrack/brewpi-script/brewpi.py") + ' --dbcfg "%s"'

def BrewPiDevice_query_db(self):
    """Query django database for active BrewPiDevices, returns an empty iterable if error"""
    try:
        return app.models.BrewPiDevice.objects.filter(status=app.models.BrewPiDevice.STATUS_ACTIVE)
    except self.model.DoesNotExist:
        self.log.info("No active {}".format(self.device_type))
    except Exception, e:
        self.log.critical("Could not query database for active devices", exc_info=self.debug)
    return []


########## Tilt Hydrometer Script Configuration
TILT_SCRIPT_CMD_TEMPLATE = "python -u " + os.path.expanduser("~/fermentrack/gravity/tilt/tilt_monitor.py") + ' --color "%s"'

def TiltConfiguration_query_db(self):
    """Query django database for active BrewPiDevices, returns an empty iterable if error"""
    try:
        return gravity.models.TiltConfiguration.objects.filter(sensor__status=gravity.models.GravitySensor.STATUS_ACTIVE)
    except self.model.DoesNotExist:
        self.log.info("No active {}".format(self.device_type))
    except Exception, e:
        self.log.critical("Could not query database for active devices", exc_info=self.debug)
    return []



########## Main Application (process spawner)

def run():
    """run - parses arguments and runs the mainloop"""

    #### Parse Arguments
    parser = argparse.ArgumentParser(prog="processmgr", formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("-i", "--interval", help="Interval between polls of the database", action="store",
                        dest="interval", type=int, default=SLEEP_INTERVAL)
    parser.add_argument("-s", "--sleep", help="Initial startup delay", action="store",
                        dest="sleep", type=int, default=2)
    parser.add_argument("-d", "--debug", help="Add debugging messages to log", action="store_true",
                        dest="debug", default=False)
    args = parser.parse_args()

    LOG.info("Settings: Start delay: {a.sleep}s, Sleep Interval: {a.interval}s, ".format(a=args))
    time.sleep(args.sleep)


    #### Create ProcessManager instances
    brewpi_process_spawner = ProcessManager(
        prefix="dev-",
        device_type="BrewPi",
        command_tmpl=BREWPI_SCRIPT_CMD_TEMPLATE,
        circus_endpoint=DEFAULT_ENDPOINT_DEALER,
        logfilepath=os.path.expanduser("~/fermentrack/log"),
        log=LOG,
        query_db_func=BrewPiDevice_query_db,
        debug=args.debug
    )

    tilt_process_spawner = ProcessManager(
        prefix="tilt-",
        device_type="Tilt",
        command_tmpl=TILT_SCRIPT_CMD_TEMPLATE,
        circus_endpoint=DEFAULT_ENDPOINT_DEALER,
        logfilepath=os.path.expanduser("~/fermentrack/log"),
        log=LOG,
        query_db_func=TiltConfiguration_query_db,
        debug=args.debug
    )

    #### Actually run the process managers
    # Replaces run_forever for all the processes
    while 1:
        brewpi_process_spawner.startstop_once()
        tilt_process_spawner.startstop_once()
        time.sleep(SLEEP_INTERVAL)

if __name__ == '__main__':
    run()


