#!/usr/bin/python

from __future__ import print_function

import os, sys

# In order to be able to use the Django ORM, we have to load everything else Django-related. Lets do that now.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fermentrack_django.settings")  # This is so Django knows where to find stuff.
sys.path.append(BASE_DIR)
os.chdir(BASE_DIR)  # This is so my local_settings.py gets loaded.
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()


import time
import getopt
import pid

import gravity.models
from gravity.tilt import TiltHydrometerFermentrack

import django.core.exceptions



# Script Defaults
verbose = False         # Should the script print out what it's doing to the console
pidFileDir = "/tmp"     # Where the pidfile should be written out to

sensor = None           # The sensor object (loaded below)
sensor_color = ''       # Color of Tilt being used - Set in the TiltConfiguration object


def print_to_stderr(*objs):
    print("", *objs, file=sys.stderr)


try:
    opts, args = getopt.getopt(sys.argv[1:], "hc:vp:l", ['help', 'color=', 'verbose', 'pidfiledir=', 'list'])
except getopt.GetoptError:
    print_to_stderr("Unknown parameter. Available options: --help, --color <color name>, --verbose, " +
                    "--pidfiledir <directory>", "--list")
    sys.exit()


for o, a in opts:
    # print help message for command line options
    if o in ('-h', '--help'):
        print_to_stderr("\r\n Available command line options: ")
        print_to_stderr("--help: Print this help message")
        print_to_stderr("--color <tilt color>: Specify the color of Tilt Hydrometer to interact with")
        print_to_stderr("--verbose: Echo readings to the console")
        print_to_stderr("--pidfiledir <directory path>: Directory to store the pidfile in")
        print_to_stderr("--list: List Tilt colors that have been set up in Fermentrack")
        exit()

    # Specify a color - required for this script to operate
    if o in ('-c', '--color'):
        sensor_color = a
        try:
            sensor = gravity.models.TiltConfiguration.objects.get(color=sensor_color)
        except django.core.exceptions.ObjectDoesNotExist:
            print_to_stderr("Color {} is not configured within Fermentrack. Exiting.".format(a))
            exit(0)

    # Echo additional information to the console
    # TODO - Determine if this should also set "DEBUG=True" for TiltHydrometerManager instances
    if o in ('-v', '--verbose'):
        verbose = True

    # Specify where the pidfile is saved out to
    if o in ('-p', '--pidfiledir'):
        if not os.path.exists(a):
            sys.exit('ERROR: pidfiledir "%s" does not exist' % a)
        pidFileDir = a

    # List out the colors currently configured in Fermentrack
    if o in ('-l', '--list'):
        try:
            dbDevices = gravity.models.TiltConfiguration.objects.all()
            print("=============== Tilt Hydrometers in Database ===============")
            if len(dbDevices) == 0:
                print("No configured devices found.")
            else:
                x = 0
                print("Available Colors:")
                for d in dbDevices:
                    x += 1
                    print("  %d: %s" % (x, d.color))
            print("============================================================")
            exit()
        except (Exception) as e:
            sys.exit(e)


if sensor is None:
    print_to_stderr("A valid color must be specified for tilt_monitor.py to operate")
    exit(0)


# check for other running instances of BrewPi that will cause conflicts with this instance
pidFile = pid.PidFile(piddir=pidFileDir, pidname="tilt_monitor_{}".format(sensor_color))
try:
    pidFile.create()
except pid.PidFileAlreadyLockedError:
    print_to_stderr("Another instance of the monitor script is running for the specified color. Exiting.")
    exit(0)


# And then start the scanner
tiltHydrometer = TiltHydrometerFermentrack.TiltHydrometerManagerFermentrack(sensor)
tiltHydrometer.loadSettings()
tiltHydrometer.start()

if verbose:
    print("Beginning to scan for color {}".format(sensor_color))

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
            print("Logging {}: {}".format(sensor_color, str(tiltValue)))

    else:
        if verbose:
            print("No data received.")

    # We're explicitly not using sensor here as the tiltHydrometer object may update tiltHydrometer.obj on its own
    time.sleep(tiltHydrometer.obj.polling_frequency)

# tiltHydrometer.stop()
