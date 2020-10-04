import os, sys

import time, datetime, getopt, pid
from typing import List, Dict

# In order to be able to use the Django ORM, we have to load everything else Django-related. Lets do that now.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fermentrack_django.settings")  # This is so Django knows where to find stuff.
sys.path.append(BASE_DIR)
os.chdir(BASE_DIR)  # This is so my local_settings.py gets loaded.
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

# This is so my local_settings.py gets loaded.

from gravity.tilt.TiltHydrometer import TiltHydrometer
import gravity.models
import django.core.exceptions

# Script Defaults
verbose = False         # Should the script print out what it's doing to the console
bluetooth_device = 0  # Default to /dev/hci0


def print_to_stderr(*objs):
    print("", *objs, file=sys.stderr)


def process_monitor_options():
    # this is ugly, and should return things instead of setting globals
    global verbose
    pid_file_dir = "/tmp"     # Where the pidfile should be written out to
    global bluetooth_device
    try:
        opts, args = getopt.getopt(sys.argv[1:], "h:vp:d:l", ['help', 'verbose', 'pidfiledir=', 'device=', 'list'])
    except getopt.GetoptError:
        print_to_stderr("Unknown parameter. Available options: --help, --verbose, " +
                        "--pidfiledir <directory> --device <device number>", "--list")
        sys.exit()

    for o, a in opts:
        # print help message for command line options
        if o in ('-h', '--help'):
            print_to_stderr("\r\n Available command line options: ")
            print_to_stderr("--help: Print this help message")
            print_to_stderr("--verbose: Echo readings to the console")
            print_to_stderr("--pidfiledir <directory path>: Directory to store the pidfile in")
            print_to_stderr("--device <device number>: The number of the bluetooth device (the X in /dev/hciX)")
            print_to_stderr("--list: List Tilt colors that have been set up in Fermentrack")
            exit()

        # Echo additional information to the console
        if o in ('-v', '--verbose'):
            verbose = True

        # Specify where the pidfile is saved out to
        if o in ('-p', '--pidfiledir'):
            if not os.path.exists(a):
                sys.exit('ERROR: pidfiledir "%s" does not exist' % a)
            pid_file_dir = a

        # Allow the user to specify an alternative bluetooth device
        if o in ('-d', '--device'):
            if not os.path.exists("/dev/hci{}".format(a)):
                sys.exit('ERROR: Device /dev/hci{} does not exist!'.format(a))
            bluetooth_device = a

        # List out the colors currently configured in Fermentrack
        if o in ('-l', '--list'):
            try:
                dbDevices = gravity.models.TiltConfiguration.objects.all()
                print("=============== Tilt Hydrometers in Database ===============")
                if len(dbDevices) == 0:
                    print("No configured devices found.")
                else:
                    x = 0
                    print("Configured Colors:")
                    for d in dbDevices:
                        x += 1
                        print("  %d: %s" % (x, d.color))
                print("============================================================")
                exit()
            except (Exception) as e:
                sys.exit(e)
  
    # check for other running instances of BrewPi that will cause conflicts with this instance
    pid_file = pid.PidFile(piddir=pid_file_dir, pidname="tilt_monitor")
    try:
        pid_file.create()
    except pid.PidFileAlreadyLockedError:
        print_to_stderr("Another instance of the monitor script is running. Exiting.")
        exit(0)
