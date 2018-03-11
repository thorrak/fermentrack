# This is the same exact file as brewpi-script/mdnsLocator.py

from __future__ import print_function
import zeroconf
from time import sleep
try:
    from models import BrewPiDevice
    djangoLoaded = True
except:
    djangoLoaded = False


class zeroconfListener(object):
    def __init__(self, print_on_discover = False):
        self.brewpi_services = {}
        self.print_on_discover = print_on_discover

    def remove_service(self, zeroconf_obj, type, name):
        if self.print_on_discover:
            print("The device at '{}' is no longer available".format(self.brewpi_services[name]['server'][:-1]))
        self.brewpi_services[name] = None

    def add_service(self, zeroconf_obj, type, name):
        info = zeroconf_obj.get_service_info(type, name)
        self.brewpi_services[name] = info
        if self.print_on_discover:
            print("Found '{}' running version '{}' of branch '{}' on a {}".format(info.server[:-1], info.properties['version'], info.properties['branch'], info.properties['board']))


def locate_brewpi_services():
    zeroconf_obj = zeroconf.Zeroconf()
    listener = zeroconfListener()
    browser = zeroconf.ServiceBrowser(zeroconf_obj, "_brewpi._tcp.local.", listener)

    sleep(3)  # We have to give zeroconf services time to respond
    zeroconf_obj.close()

    return listener.brewpi_services


def find_mdns_devices():
    services = locate_brewpi_services()

    installed_devices = []
    available_devices = []
    found_device = {}

    for this_service in services:
        found_device['mDNSname'] = services[this_service].server[:-1]
        found_device['board'] = services[this_service].properties['board']
        found_device['branch'] = services[this_service].properties['branch']
        found_device['revision'] = services[this_service].properties['revision']
        found_device['version'] = services[this_service].properties['version']

        if djangoLoaded:  # Breaking this out so that we can have this be a direct clone for brewpi-script
            try:
                # If we found the device, then we're golden - it's already installed (in theory)
                found_device['device'] = BrewPiDevice.objects.get(wifi_host=found_device['mDNSname'])
                installed_devices.append(found_device.copy())
            except:
                found_device['device'] = None
                available_devices.append(found_device.copy())
        else:
            found_device['device'] = None
            available_devices.append(found_device.copy())

    return installed_devices, available_devices


if __name__ == '__main__':
    # zeroconf_obj = zeroconf.Zeroconf()
    # listener = zeroconfListener()
    # browser = zeroconf.ServiceBrowser(zeroconf_obj, "_brewpi._tcp.local.", listener)

    print("Scanning for available mDNS devices")
    _, available_devices = find_mdns_devices()

    for this_device in available_devices:
        print("Found Device: {} - Board {} - Branch {} - Revision {}".format(this_device['mDNSname'],
                                                                             this_device['board'],
                                                                             this_device['branch'],
                                                                             this_device['revision']))
    print("All found devices listed. Exiting.")
    # try:
    #     input("Press enter to exit...\n\n")
    # finally:
    #     zeroconf_obj.close()