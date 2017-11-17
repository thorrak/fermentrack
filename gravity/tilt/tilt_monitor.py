#!/usr/bin/python


import TiltHydrometerFermentrack
import time
import redis
import gravity.models







tiltHydrometer = TiltHydrometerFermentrack.TiltHydrometerManager(False, 60, 40)
tiltHydrometer.loadSettings()
tiltHydrometer.start()
memcache_client = pymemcache.client.base.Client(('localhost', 11211))


def toString(value):
    returnValue = value
    if value is None:
        returnValue = ''
    return str(returnValue)


print "Startup Value for Purple: {}".format(memcache_client.get('Purple'))
print "Scanning - 20 Secs (Control+C to exit early)"
for num in range(1, 120):
    for colour in TiltHydrometer.TILTHYDROMETER_COLOURS:
        tiltValue = tiltHydrometer.getValue(colour)
        print colour + ": " + str(tiltValue)
        if tiltValue is not None:
            memcache_client.set(colour, tiltValue)

    time.sleep(10)

tiltHydrometer.stop()
