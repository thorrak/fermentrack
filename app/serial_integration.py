import serial.tools.list_ports

import pickle

import udev_integration

DEVICE_CACHE_FILENAME = 'device.cache'

known_devices = {
    'arduino': [
        # Those with 'generic': False are virtually guaranteed to be Arduinos
        {'vid': 0x2341, 'pid': 0x0010, 'name': "Arduino Mega2560",  'generic': False},
        {'vid': 0x2341, 'pid': 0x8036, 'name': "Arduino Leonardo",  'generic': False},
        {'vid': 0x2341, 'pid': 0x0036, 'name': "Arduino Leonardo Bootloader", 'generic': False},
        {'vid': 0x2341, 'pid': 0x0043, 'name': "Arduino Uno",       'generic': False},
        {'vid': 0x2341, 'pid': 0x0001, 'name': "Arduino Uno",       'generic': False},
        {'vid': 0x2a03, 'pid': 0x0010, 'name': "Arduino Mega2560",  'generic': False},
        {'vid': 0x2a03, 'pid': 0x8036, 'name': "Arduino Leonardo",  'generic': False},
        {'vid': 0x2a03, 'pid': 0x0036, 'name': "Arduino Leonardo Bootloader", 'generic': False},
        {'vid': 0x2a03, 'pid': 0x0043, 'name': "Arduino Uno",       'generic': False},
        {'vid': 0x2a03, 'pid': 0x0001, 'name': "Arduino Uno",       'generic': False},

        # While those with 'generic': True use a generic USB to UART bridge
        {'vid': 0x1a86, 'pid': 0x7523, 'name': "Generic USB-Serial Chip", 'generic': True},
        {'vid': 0x1D50, 'pid': 0x607D, 'name': "Generic CP2104 USB-Serial Chip", 'generic': True},  # Not sure if this is used on any Arduino clones
    ],
    'particle': [
        {'vid': 0x1D50, 'pid': 0x607D, 'name': "Particle Core",     'generic': True},  # Particle Core uses a generic CP2104 SLAB USBtoUART Chip
        {'vid': 0x2B04, 'pid': 0xC006, 'name': "Particle Photon",   'generic': False},
        {'vid': 0x2B04, 'pid': 0xC006, 'name': "Particle Photon",   'generic': False},
    ],
    'esp8266': [
        {'vid': 0x1D50, 'pid': 0x607D, 'name': "Generic CP2104 USB-Serial Chip", 'generic': True},
    ]
}

def check_known_devices(family, pid, vid, return_bool=False):
    unknown_device = {'name': "Unknown", 'generic': True}

    if family not in known_devices:
        if return_bool:
            return False
        else:
            return unknown_device

    device_list = known_devices[family]

    for this_device in device_list:
        if this_device['vid'] == vid and this_device['pid'] == pid:
            if return_bool:
                return True
            else:
                return {'name': this_device['name'], 'generic': this_device['generic']}

    if return_bool:
        return False
    else:
        return unknown_device


def write_list_to_file(devices, filename):
    with open(filename, 'wb') as fp:
        pickle.dump(devices, fp)


def read_list_from_file(filename):
    with open(filename, 'rb') as fp:
        devices = pickle.load(fp)
    return devices


def cache_current_devices():
    ports = list(serial.tools.list_ports.comports())

    current_devices=[]
    for p in ports:
        current_devices.append(p.device)

    write_list_to_file(current_devices, DEVICE_CACHE_FILENAME)

    return current_devices


def compare_current_devices_against_cache(family="arduino"):
    ports = list(serial.tools.list_ports.comports())

    # We read current_devices the same as above
    current_devices=[]
    for p in ports:
        current_devices.append(p.device)

    # We read in existing_devices from the device.cache file we (presumably) created earlier
    existing_devices = read_list_from_file(DEVICE_CACHE_FILENAME)

    # New devices is any device that shows now (but didn't show before)
    new_devices = list(set(current_devices) - set(existing_devices))

    # Once we have current_devices, existing_devices, and new_devices, let's enrich new_devices
    new_devices_enriched = []
    for p in ports:
        if p.device in new_devices:
            known_device = check_known_devices(family, p.pid, p.vid)
            enriched_device = {'vid': p.vid, 'pid': p.pid, 'device': p.device, 'description': p.description,
                               'known_name': known_device['name'], 'known_generic': known_device['generic']}
            new_devices_enriched.append(enriched_device)

    # And now, let's return all four lists for good measure. We can discard the ones we don't want.
    return existing_devices, current_devices, new_devices, new_devices_enriched



# The following was used for testing during development
if __name__ == "__main__":
    # cache_current_devices()
    existing_devices, current_devices, new_devices, new_devices_enriched = compare_current_devices_against_cache("arduino")

    pass