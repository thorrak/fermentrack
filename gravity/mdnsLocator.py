# This file is specifically intended to be used to locate TiltBridge devices

from __future__ import print_function
import zeroconf
from time import sleep

from gravity.models import TiltBridge


class ZeroconfListener(object):
    def __init__(self, print_on_discover=False):
        self.tiltbridge_services = {}
        self.print_on_discover = print_on_discover

    def remove_service(self, zeroconf_obj, type, name):
        if self.print_on_discover:
            print("The device at '{}' is no longer available".format(self.tiltbridge_services[name]['server'][:-1]))
        self.tiltbridge_services[name] = None

    def add_service(self, zeroconf_obj, type, name):
        info = zeroconf_obj.get_service_info(type, name)
        self.tiltbridge_services[name] = info
        if self.print_on_discover:
            # print("Found '{}' running version '{}' of branch '{}' on a {}".format(info.server[:-1], info.properties['version'], info.properties['branch'], info.properties['board']))
            print("Found TiltBridge '{}.local' with API key {}".format(info.server[:-1], info.properties['api_key']))


def locate_tiltbridge_services():
    zeroconf_obj = zeroconf.Zeroconf()
    listener = ZeroconfListener()
    browser = zeroconf.ServiceBrowser(zeroconf_obj, "_tiltbridge._tcp.local.", listener)

    sleep(3)  # We have to give zeroconf services time to respond
    zeroconf_obj.close()

    return listener.tiltbridge_services


def find_mdns_devices():
    services = locate_tiltbridge_services()

    installed_tiltbridges = []
    available_tiltbridges = []
    found_device = {}

    for this_service in services:
        found_device['mDNSname'] = services[this_service].server[:-1]
        found_device['api_key'] = services[this_service].properties[b'api_key'].decode(encoding='cp437')
        # found_device['branch'] = services[this_service].properties[b'branch'].decode(encoding='cp437')
        # found_device['revision'] = services[this_service].properties[b'revision'].decode(encoding='cp437')
        # found_device['version'] = services[this_service].properties[b'version'].decode(encoding='cp437')

        try:
            # If we found the device, then we're golden - it's already installed (in theory)
            found_device['device'] = TiltBridge.objects.get(api_key=found_device['api_key'])
            installed_tiltbridges.append(found_device.copy())
        except:
            found_device['device'] = None
            available_tiltbridges.append(found_device.copy())

    return installed_tiltbridges, available_tiltbridges


if __name__ == '__main__':
    # zeroconf_obj = zeroconf.Zeroconf()
    # listener = zeroconfListener()
    # browser = zeroconf.ServiceBrowser(zeroconf_obj, "_tiltbridge._tcp.local.", listener)

    print("Scanning for available mDNS devices")
    _, available_devices = find_mdns_devices()

    for this_device in available_devices:
        # print("Found Device: {} - Board {} - Branch {} - Revision {}".format(this_device['mDNSname'],
        #                                                                      this_device['board'],
        #                                                                      this_device['branch'],
        #                                                                      this_device['revision']))
        print("Found Device: {} - API Key {}".format(this_device['mDNSname'], this_device['api_key'],))

    print("All found devices listed. Exiting.")
    # try:
    #     input("Press enter to exit...\n\n")
    # finally:
    #     zeroconf_obj.close()