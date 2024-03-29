#!/usr/bin/env python

# This is a process manager used for launching individual instances of BrewPi-script for each valid configuration in
# a Fermentrack database.

import time
import atexit
from multiprocessing import Process
from fermentrack_config_loader import FermentrackBrewPiScriptConfig, get_active_brewpi_devices
from brewpi import BrewPiScript
import sentry_sdk

sentry_sdk.init(
    "https://f22697f646434bdca503eb1394f5bdc7@sentry.optictheory.com/4",
    traces_sample_rate=0.0
)


def cleanup(process_list):
    """Ensures all child processes are terminated and joined before exiting."""
    for pid, process in process_list.items():
        if process.is_alive():
            process.terminate()
            process.join()


if __name__ == '__main__':
    process_list = {}
    config_list = {}

    atexit.register(cleanup, process_list)

    while 1:
        # Clean out dead processes from the process list
        processes_to_delete = []
        for this_process in process_list:
            if not process_list[this_process].is_alive():
                processes_to_delete.append(this_process)
        for this_process in processes_to_delete:
            # Do this as step 2 since we can't change the process list mid-iteration
            process_list[this_process].join(10)
            if process_list[this_process].is_alive():  # Check if process is still alive after join
                process_list[this_process].terminate()  # Force terminate if it's still alive
            del process_list[this_process]

        active_device_ids = get_active_brewpi_devices()

        # Launch any processes that are missing from the process list
        for this_id in active_device_ids:
            if this_id not in process_list:
                # The process hasn't been spawned. Spawn it.
                # print(f"Launching process for BrewPiDevice #{this_id}")
                if this_id in config_list:
                    config_list.pop(this_id)
                try:
                    config_list[this_id] = FermentrackBrewPiScriptConfig(brewpi_device_id=this_id)
                    config_list[this_id].load_from_fermentrack(False)
                    process_list[this_id] = Process(target=BrewPiScript, args=(config_list[this_id], ))
                    process_list[this_id].start()
                    time.sleep(10)  # Give each controller 10 seconds to start up
                except StopIteration:
                    pass
                except Exception as e:  # Handle other exceptions
                    sentry_sdk.capture_exception(e)  # Send the exception to Sentry
                    print(f"Error while launching process for BrewPiDevice #{this_id}: {e}")

        time.sleep(5)  # Wait 5 seconds in each loop
