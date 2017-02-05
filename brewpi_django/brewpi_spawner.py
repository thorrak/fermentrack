import os
import sys
import time
from circus.client import CircusClient
from circus.util import DEFAULT_ENDPOINT_DEALER

# Load up the Django specific stuff
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# This is so Django knows where to find stuff.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "brewpi_django.settings")
sys.path.append(BASE_DIR)
from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
import app.models as models

# Constants
SLEEP_INTERVAL = 15


def spawnBrewpi(name):
    """Spawn a new brewpi.py process via circus, 'dev-' is appended to the name to
    keep brewpi devices seperated from other devices
    """
    client = CircusClient(endpoint=DEFAULT_ENDPOINT_DEALER)
    commandTmpl = 'python -u brewpi-script/brewpi.py --dbcfg %s'
    procName = "dev-%s" % name
    try:
        call = client.call(
            {
                "command": "add",
                "properties": {
                    "cmd": commandTmpl % name,
                    "name": procName,
                    "options": {
                        "copy_env": True,
                        "stdout_stream": {
                            "class": "FileStream",
                            "filename": "log/%s-stdout.log" % procName
                        },
                        "stderr_stream": {
                            "class": "FileStream",
                            "filename": "log/%s-stderr.log" % procName,
                        }
                    },
                    "start": True
                }
            }
        )
    except Exception, e:
        print("Error spawning process: %s", str(e))


def stopAndRemoveDevice(name):
    client = CircusClient(endpoint=DEFAULT_ENDPOINT_DEALER)
    cmdStop = {
        "command": "stop",
        "properties": {
            "waiting": False,
            "name": name,
            "match": "glob"
        }
    }
    cmdRm = {
        "command": "rm",
        "properties": {"name": name}
    }
    callStop = client.call(cmdStop)
    callRm = client.call(cmdRm)


def getRunningBrewpiDevices():
    client = CircusClient()
    call = client.call({"command": "list", "properties": {}})
    return call['watchers']


def RunAndStopDevices():
    dbDevices = models.BrewPiDevice.objects.all()
    runningDevices = [x for x in getRunningBrewpiDevices() if x.startswith("dev-")]
    names = []
    # Find non running devices
    for dbd in dbDevices:
        devName = "dev-" + dbd.device_name
        names.append(devName)
        if devName not in runningDevices:
            print "Should start: %s" % devName
            spawnBrewpi(dbd.device_name)
    # Find devices running but should not
    for rdev in runningDevices:
        if rdev not in names:
            print "Should be stopped: %s" % rdev
            stopAndRemoveDevice(rdev)


def loopForever():
    while 1:
        RunAndStopDevices()
        time.sleep(SLEEP_INTERVAL)


def main():
    loopForever()


if __name__ == '__main__':
    main()