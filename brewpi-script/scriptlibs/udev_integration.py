
try:
    import pyudev
    pyudev_available = True
except:
    pyudev_available = False

import sys


def get_platform():
    platforms = {
        'linux': 'Linux',
        'linux1': 'Linux',
        'linux2': 'Linux',
        'darwin': 'OS X',
        'win32': 'Windows'
    }
    if sys.platform not in platforms:
        return sys.platform

    return platforms[sys.platform]

def valid_platform_for_udev():
    if get_platform() != "Linux":
        return False
    else:
        return pyudev_available

# get_serial_from_node() takes a "node" (/dev/TTYUSB0) and returns the serial number of the device (Silicon_Labs_CP2104_USB_to_UART_Bridge_Controller_011E8348)
def get_serial_from_node(device_node):
    try:
        context = pyudev.Context()

        for device in context.list_devices(subsystem="tty"):
            if device.device_node == device_node:
                return device.get("ID_SERIAL")
    except:
        # We weren't able to use pyudev (possibly because of an invalid operating system)
        pass
    return None


# get_node_from_serial() takes a udev serial number, and retuns the associated node (if found)
def get_node_from_serial(device_serial):
    try:
        context = pyudev.Context()

        for device in context.list_devices(subsystem="tty"):
            if device.get("ID_SERIAL", "") == device_serial:
                return device.device_node
    except:
        # We weren't able to use pyudev (possibly because of an invalid operating system)
        pass
    return None


# The following was used for testing during development
if __name__ == "__main__":
    print(get_platform())
    context = pyudev.Context()
    serial_from_node = get_serial_from_node("/dev/ttyUSB0")
    node_from_serial = get_node_from_serial(serial_from_node)

    print(u'{} ({})'.format(serial_from_node, node_from_serial))
