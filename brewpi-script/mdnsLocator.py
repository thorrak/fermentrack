import zeroconf
from time import sleep


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
    # This error was fixed in a recent version of zeroconf
    # print("NOTE - An error message from 'zeroconf' may appear below. Ignore it - it is working as intended.")
    zeroconf_obj = zeroconf.Zeroconf()
    listener = zeroconfListener()
    browser = zeroconf.ServiceBrowser(zeroconf_obj, "_brewpi._tcp.local.", listener)

    sleep(3)  # We have to give zeroconf services time to respond
    zeroconf_obj.close()

    return listener.brewpi_services


if __name__ == '__main__':
    zeroconf_obj = zeroconf.Zeroconf()
    listener = zeroconfListener()
    browser = zeroconf.ServiceBrowser(zeroconf_obj, "_brewpi._tcp.local.", listener)
    try:
        input("Press enter to exit...\n\n")
    finally:
        zeroconf_obj.close()