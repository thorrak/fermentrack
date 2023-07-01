#!/usr/bin/env python

# This is a process manager used for launching individual instances of BrewPi-script for each valid configuration in
# a Fermentrack database.

import time
from multiprocessing import Process

from fermentrack_config_loader import FermentrackBrewPiScriptConfig, get_active_brewpi_devices
from brewpi import BrewPiScript

import sentry_sdk
sentry_sdk.init(
    "http://645d7f33bc4f427daf87fbe57289a3fc@sentry.optictheory.com:9000/13",

    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # We recommend adjusting this value in production.
    traces_sample_rate=0.0
)

if __name__ == '__main__':
    process_list = {}
    config_list = {}

    while 1:
        # Clean out dead processes from the process list
        processes_to_delete = []
        for this_process in process_list:
            if not process_list[this_process].is_alive():
                processes_to_delete.append(this_process)
        for this_process in processes_to_delete:
            # Do this as step 2 since we can't change the process list mid-iteration
            # print(f"Deleting process for BrewPiDevice #{this_process}")
            # process_list[this_process].join(5)  # Join the completed process
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
                except StopIteration:
                    pass
                else:
                    process_list[this_id] = Process(target=BrewPiScript, args=(config_list[this_id], ))
                    process_list[this_id].start()
                time.sleep(10)  # Give each controller 10 seconds to start up

        time.sleep(5)  # Wait 5 seconds in each loop
