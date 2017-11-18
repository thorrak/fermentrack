#!/usr/bin/python

import os, sys

# For Fermentrack compatibility, try to load the Django includes. If we fail, keep running, just set djangoLoaded
# as false. If it turns out the user tried to launch with dblist/dbcfg, die with an error message.
# Load up the Django specific stuff
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fermentrack_django.settings")  # This is so Django knows where to find stuff.
sys.path.append(BASE_DIR)
os.chdir(BASE_DIR)  # This is so my local_settings.py gets loaded.
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()


import time
import redis

import gravity.models
import TiltHydrometerFermentrack



# For now, I'm explicitly testing with 'pink' because that's the closest one to where I'm sitting
sensor_color = 'Pink'
verbose = True
loop_delay = 10  # Time between log readings (in seconds)

# Load the sensor object associated with the sensor color we were provided
sensor = gravity.models.TiltConfiguration.objects.get(color=sensor_color)

# And then start the scanner
tiltHydrometer = TiltHydrometerFermentrack.TiltHydrometerManagerFermentrack(sensor)
tiltHydrometer.loadSettings()
tiltHydrometer.start()

if verbose:
    print "Beginning to scan for color {}".format(sensor_color)

while True:
    tiltValue = tiltHydrometer.getValue(sensor_color)
    if tiltValue is not None:
        new_point = gravity.models.GravityLogPoint(
            gravity=tiltValue.gravity,
            temp=tiltValue.temperature,
            temp_format=tiltHydrometer.obj.sensor.temp_format,
            temp_is_estimate = False,
            associated_device=tiltHydrometer.obj.sensor,
        )

        if tiltHydrometer.obj.sensor.active_log is not None:
            new_point.associated_log = tiltHydrometer.obj.sensor.active_log

        new_point.save()

        if verbose:
            print "Logging {}: {}".format(sensor_color, str(tiltValue))

    else:
        if verbose:
            print "No data received."

    time.sleep(loop_delay)

# tiltHydrometer.stop()
