import time
from multiprocessing import Process

from hardcodeDbConfig import HardcodedDBConfig
from brewpi import BrewPiScript


if __name__ == '__main__':
    process_list = {}
    dbc_list = {}

    dbc_list['p1'] = HardcodedDBConfig("5564", "192.168.5.115")
    dbc_list['p2'] = HardcodedDBConfig("5569", "192.168.5.184")

    # p1 = Process(target=BrewPiScript, args=(dbc_list['p1'], False))
    # p1.start()
    # p1.join()

    # p2 = Process(target=BrewPiScript, args=(dbc_list['p2'], False))
    # p2.start()
    # p2.join()

    while 1:
        # Clean out dead processes from the process list
        processes_to_delete = []
        for this_process in process_list:
            if not process_list[this_process].is_alive():
                processes_to_delete.append(this_process)
        for this_process in processes_to_delete:
            # Do this as step 2 since we can't change the process list mid-iteration
            print(f"Deleting process {this_process}")
            del process_list[this_process]

        # Launch any processes that are missing from the process list
        for this_dbc in dbc_list:
            if this_dbc not in process_list:
                # The process hasn't been spawned. Spawn it.
                print(f"Launching process {this_dbc}")
                process_list[this_dbc] = Process(target=BrewPiScript, args=(dbc_list[this_dbc], ))
                process_list[this_dbc].start()

        time.sleep(2)

        # print(f"Process 1: {p1.is_alive()}, Process 2: {p2.is_alive()}")
