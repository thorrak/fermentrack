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
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "brewpi_django.settings")
sys.path.append(BASE_DIR)
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
import app.models as models

LOG = logging.getLogger("brewpi-spawner")
LOG.setLevel(logging.DEBUG)

# Constants
SLEEP_INTERVAL = 15


class BrewPiSpawner(object):
    """Handles spawning and stopping BrewPi devices defined in brewpi-django database"""
    def __init__(self, model,
                 prefix="dev-",
                 sleep_interval=SLEEP_INTERVAL,
                 command_tmpl='python -u brewpi-script/brewpi.py --dbcfg %s',
                 circus_endpoint=DEFAULT_ENDPOINT_DEALER,
                 log=LOG
                ):
        self.prefix = prefix
        self.command_tmpl = command_tmpl
        self.model = model
        self.sleep_interval = sleep_interval
        self.circus_endpoint = circus_endpoint
        self.log = log


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
        client = CircusClient(endpoint=self.circus_endpoint)
        try:
            call = client.call({"command": "list", "properties": {}})
        except CallError:
            self.log.error("Could not get running processes", exc_info=True)
            return []
        running_devices = [x for x in call['watchers'] if x.startswith(self.prefix)]
        return running_devices


    def startstop_once(self):
        """Checks for active devices in database, compares to running, starts and stops based on
        if device should be running or not
        """
        db_devices = self._querydb()
        self.log.debug("db_devices: %s", str(db_devices))
        # Only get devices that are run within circus with the prefix
        running_devices = self._running()
        self.log.debug("running_devices: %s", running_devices)
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
        client = CircusClient(endpoint=self.circus_endpoint)
        proc_name = self.prefix + name
        # https://github.com/circus-tent/circus/issues/927
        proc_name = proc_name.lower()
        try:
            call = client.call(
                {
                    "command": "add",
                    "properties": {
                        "cmd": self.command_tmpl % name,
                        "name": proc_name,
                        "options": {
                            "copy_env": True,
                            "stdout_stream": {
                                "class": "FileStream",
                                "filename": "log/%s-stdout.log" % proc_name
                            },
                            "stderr_stream": {
                                "class": "FileStream",
                                "filename": "log/%s-stderr.log" % proc_name,
                            }
                        },
                        "start": True
                    }
                }
            )
            self.log.debug("_add_process circus client call: %s", str(call))
        except CallError:
            self.log.error("Could not spawn process: %s", proc_name, exc_info=True)


    def _stop_process(self, name):
        client = CircusClient(endpoint=self.circus_endpoint)
        # https://github.com/circus-tent/circus/issues/927
        name = name.lower()
        cmd_stop = {
            "command": "stop",
            "properties": {
                "waiting": False,
                "name": name,
                "match": "glob"
            }
        }
        try:
            call_stop = client.call(cmd_stop)
            self.log.debug("_stop_process circus client call: %s", str(call_stop))
        except CallError:
            self.log.debug("Could not stop process: %s", name, exc_info=True)


    def _rm_process(self, name):
        client = CircusClient(endpoint=self.circus_endpoint)
        # https://github.com/circus-tent/circus/issues/927
        name = name.lower()
        cmd_rm = {
            "command": "rm",
            "properties": {"name": name}
        }
        try:
            call_rm = client.call(cmd_rm)
            self.log.debug("_rm_device circus client call: %s", str(call_rm))
        except CallError:
            self.log.debug("Could not rm process: %s", name, exc_info=True)


    def run_forvever(self):
        """Runs startstop_onece every sleep_interval"""
        while 1:
            self.startstop_once()
            time.sleep(self.sleep_interval)


if __name__ == '__main__':
    # Chill so that circus has time to startup
    time.sleep(5)
    process_spawner = BrewPiSpawner(model=models.BrewPiDevice, prefix="dev-")
    process_spawner.run_forvever()

