import serial.tools.list_ports


known_devices = {
    'arduino': [
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

        {'vid': 0x1a86, 'pid': 0x7523, 'name': "Generic USB-Serial Chip", 'generic': True},
    ],
    'particle': [
        {'vid': 0x1D50, 'pid': 0x607D, 'name': "Particle Core",     'generic': False},
        {'vid': 0x2B04, 'pid': 0xC006, 'name': "Particle Photon",   'generic': False},
        {'vid': 0x2B04, 'pid': 0xC006, 'name': "Particle Photon",   'generic': False},
    ],
    'esp8266': [
        {},
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


ports = list(serial.tools.list_ports.comports())
for p in ports:

    device_description = p.description
    device_device = p.device
    device_pid = p.pid
    device_vid = p.vid

    known_device = check_known_devices("arduino", device_pid, device_vid)


    print p