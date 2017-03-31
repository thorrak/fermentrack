import os
import sys
import time
import logging

from circus.client import CircusClient
from circus.exc import CallError
from circus.util import DEFAULT_ENDPOINT_DEALER

# Load up the Django specific stuff
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# This is so Django knows where to find stuff.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fermentrack_django.settings")
sys.path.append(BASE_DIR)
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
import app.models as models
from lib.ftcircus.client import CircusMgr, CircusException

LOG = logging.getLogger("processmgr")
LOG.setLevel(logging.DEBUG)

# Constants
SLEEP_INTERVAL = 15
DEFAULT_CMD_TEMPLATE = "python -u " + os.path.expanduser("~/fermentrack/brewpi-script/brewpi.py") + ' --dbcfg "%s"'


class BrewPiSpawner(object):
    """Handles spawning and stopping BrewPi devices defined in Fermentrack database"""
    def __init__(self, model,
                 prefix="dev-",
                 sleep_interval=SLEEP_INTERVAL,
                 command_tmpl='python -u brewpi-script/brewpi.py --dbcfg %s',
                 circus_endpoint=DEFAULT_ENDPOINT_DEALER,
                 logfilepath=os.path.expanduser("~/fermentrack/log"),
                 log=LOG
                ):
        self.prefix = prefix
        self.command_tmpl = command_tmpl
        self.model = model
        self.sleep_interval = sleep_interval
        self.circus_endpoint = circus_endpoint
        self.logfilepath = logfilepath
        self.log = log
        self._cm = CircusMgr(circus_endpoint=circus_endpoint)


    def _querydb(self):
        """Query django database for active devices, returns an empty iterable if error"""
        try:
            return self.model.objects.filter(status='active')
        except self.model.DoesNotExist:
            self.log.info("No active devices")
        except Exception, e:
            self.log.info("Could not query database for active devices", exc_info=True)
        return []


    def _running(self):
        """Return Brewpi instances running using suffix as filter"""
        try:
            watchers = self._cm.get_applications()
        except CircusException:
            self.log.error("Could not get running processes", exc_info=True)
            return []
        running_devices = [x for x in watchers if x.startswith(self.prefix)]
        return running_devices


    def startstop_once(self):
        """Checks for active devices in database, compares to running, starts and stops based on
        if device should be running or not
        """
        db_devices = self._querydb()
        self.log.debug("db_devices: %s", ", ".join([dev.device_name for dev in db_devices]))
        # Only get devices that are run within circus with the prefix
        running_devices = self._running()
        self.log.debug("db_devices: %s", ", ".join([dev for dev in running_devices]))
        names = []
        # Find non running devices
        for dbd in db_devices:
            dev_name = self.prefix + dbd.device_name
            # https://github.com/circus-tent/circus/issues/927
            dev_name = dev_name.lower()
            names.append(dev_name)
            if dev_name not in running_devices:
                self.log.info("New BrewPi device found: %s", dev_name.lower())
                self._add_process(dbd.device_name)

        # Find devices running but should not
        for rdev in running_devices:
            if rdev not in names:
                self.log.info("Device: %s should be stopped, stopping", rdev)
                self._stop_process(rdev)
                self._rm_process(rdev)


    def _add_process(self, name):
        """Spawn a new brewpi.py process via circus, 'dev-' is appended to the name to
        keep brewpi devices seperated from other devices
        """
        proc_name = self.prefix + name
        # https://github.com/circus-tent/circus/issues/927
        proc_name = proc_name.lower()
        cmd = self.command_tmpl % name
        try:
            call = self._cm.add_controller(
                cmd,
                proc_name,
                self.logfilepath
            )
            self.log.debug("_add_process circus client call")
        except CircusException:
            self.log.error("Could not spawn process: %s", proc_name, exc_info=True)


    def _stop_process(self, name):
        # https://github.com/circus-tent/circus/issues/927
        name = name.lower()
        try:
            self._cm.stop(name)
            self.log.debug("_stop_process circus client call")
        except CircusException:
            self.log.debug("Could not stop process: %s", name, exc_info=True)


    def _rm_process(self, name):
        # https://github.com/circus-tent/circus/issues/927
        name = name.lower()
        try:
            self._cm.remove(name)
            self.log.debug("_rm_device circus client call")
        except CircusException:
            self.log.debug("Could not rm process: %s", name, exc_info=True)


    def run_forvever(self):
        """Runs startstop_onece every sleep_interval"""
        while 1:
            self.startstop_once()
            time.sleep(self.sleep_interval)


if __name__ == '__main__':
    # Chill so that circus has time to startup
    LOG.debug("Starting up, wait 2s for everything to get ready")
    time.sleep(2)
    process_spawner = BrewPiSpawner(model=models.BrewPiDevice, command_tmpl=DEFAULT_CMD_TEMPLATE, prefix="dev-")
    process_spawner.run_forvever()

