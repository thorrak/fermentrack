# gravity_debug.py is designed to be a test suite to ensure that the packages for specific gravity support are installed
# and to assist with debugging anything that isn't working properly. The idea is that gravity support was added later
# in the development cycle of Fermentrack and therefore cannot be assumed to be working out of the box.

from fermentrack_django import settings

import uuid

try:
    import redis
    redis_installed = True
except:
    redis_installed = False


def try_redis(host=settings.REDIS_HOSTNAME, port=settings.REDIS_PORT, password=settings.REDIS_PASSWORD) -> (bool, bool, bool):
    # Returns a tuple: (redis_installed, able_to_connect_test_result, key_set_and_retreival_test_result)

    if not redis_installed:
        # If we don't have the redis libraries, we can't exactly do anything else...
        return False, False, False

    try:

        r = redis.Redis(host=host, port=port, password=password, socket_timeout=3)
        r.ping()  # Test if the connection is active
    except redis.exceptions.TimeoutError:
        # Connection timed out (was unavailable). Report back that the test failed
        return True, False, False
    except redis.exceptions.ConnectionError:
        # Other onnection error. Report back that the test failed
        return True, False, False


    # Generate a unique value to use for testing if we can set values on Redis
    key_value = str(uuid.uuid4())

    # Now, set it, read it back, and test that they're equal
    r.set('test_key', key_value.encode(encoding="utf-8"))
    returned_value = r.get('test_key').decode(encoding="utf-8")
    if returned_value == key_value:
        return True, True, True
    else:
        return True, True, False


# The following was used for testing during development, and is a standalone test that can be run if needed
if __name__ == "__main__":
    # Setting these here for the standalone test
    # redis_host = '127.0.0.2'
    # redis_port = 6379
    # redis_pass = ''

    # redis_install_test, redis_connection_test, redis_value_test = try_redis(redis_host, redis_port, redis_pass)
    redis_install_test, redis_connection_test, redis_value_test = try_redis()

    print("Redis Installed: {}".format(redis_install_test))
    # print("Testing redis connection to ({},{},{}):".format(redis_host, redis_port, redis_pass))
    print("Testing redis connection to ({},{},{}):".format(settings.REDIS_HOSTNAME, settings.REDIS_PORT, settings.REDIS_PASSWORD))
    print("Connection Test: {}".format(redis_connection_test))
    print("Value Set/Read Test: {}".format(redis_value_test))

