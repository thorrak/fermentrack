#!/usr/bin/env python

# This is a class used for managing processes within Fermentrack. Each instance of this class is designed to track one
# type of process driven by one type of model (ie - brewpi_script, tilt_manager, etc.)


import os, sys
import time
import logging

# from circus.client import CircusClient
# from circus.exc import CallError
# from circus.util import DEFAULT_ENDPOINT_DEALER

# Amend the base to the path so we can include lib.ftcircus.client
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from lib.ftcircus.client import CircusMgr, CircusException


class ProcessManager(object):
    """Handles spawning and stopping processes associated with devices defined in Fermentrack database"""
    def __init__(self, prefix, device_type, command_tmpl, circus_endpoint, logfilepath, log, query_db_func, debug=False):
        # prefix          - Subprocess name prefix (used for tracking/logging)
        # device_type     - The human readable device type (for logging)
        # command_tmpl    - Command template for launching subprocess
        # circus_endpoint - The endpoint of the circus instance to interact with
        # logfilepath     - The filepath to store log info associated with spawned processes
        # log             - The logger to use
        # debug           - Boolean - defines if we should print debug information
        # query_db_func   - Function (passed into this object) which retrieves all devices which need an active process

        # _querydb        - query_db_func passed in above
        # _circusmgr      - Circus manager object (not passed in)

        self.prefix = prefix
        self.device_type = device_type
        self.command_tmpl = command_tmpl
        self.circus_endpoint = circus_endpoint
        self.logfilepath = logfilepath
        self.log = log
        self.debug = debug

        self._querydb = query_db_func
        self._circusmgr = CircusMgr(circus_endpoint=circus_endpoint)
        if self.debug:
            self.log.setLevel(logging.DEBUG)

    def _running(self):
        """Return running instances running using suffix as filter"""
        try:
            watchers = self._circusmgr.get_applications()
        except CircusException:
            self.log.error("Could not get running processes from circus", exc_info=self.debug)
            return []
        # Only pic devices with prefix set, other apps are other functions and should be left alone.
        running_devices = [x for x in watchers if x.startswith(self.prefix)]
        return running_devices


    def startstop_once(self):
        """Checks for active devices in database, compares to running, starts and stops based on
        if device should be running or not
        """
        # Get all devices from database
        db_devices = self._querydb(self)
        # Only get devices that are run within circus with the prefix
        running_devices = self._running()

        self.log.debug(
            "DB devices (active): %s, Running device processes: %s",
            ", ".join([dev.circus_parameter() for dev in db_devices]),
            ", ".join([dev for dev in running_devices])
            )
        names = []
        # Find active but non-running devices
        for dbd in db_devices:
            dev_name = self.prefix + dbd.circus_parameter()
            # https://github.com/circus-tent/circus/issues/927
            dev_name = dev_name.lower()
            names.append(dev_name)
            if dev_name not in running_devices:
                self.log.info("New {} device found: {}".format(self.device_type, dev_name))
                self._add_process(dbd.circus_parameter())

        # Find devices running but should not
        for rdev in running_devices:
            if rdev not in names:
                self.log.info("Device: %s should be stopped and removed, stopped", rdev)
                self._rm_process(rdev)


    def _add_process(self, name):
        # Spawn a new process via circus. <self.prefix> is prepended to the name to keep each process's devices separate
        proc_name = self.prefix + name
        # https://github.com/circus-tent/circus/issues/927
        proc_name = proc_name.lower()
        cmd = self.command_tmpl % name
        try:
            call = self._circusmgr.add_controller(cmd, proc_name, self.logfilepath)
            self.log.debug("_add_process circus client call")
        except CircusException:
            self.log.error("Could not spawn process: %s", proc_name, exc_info=self.debug)


    def _stop_process(self, name):
        # https://github.com/circus-tent/circus/issues/927
        name = name.lower()
        try:
            self._circusmgr.stop(name)
            self.log.debug("_stop_process circus client call")
        except CircusException:
            self.log.debug("Could not stop process: %s", name, exc_info=self.debug)


    def _rm_process(self, name):
        # https://github.com/circus-tent/circus/issues/927
        name = name.lower()
        try:
            self._circusmgr.remove(name)
            self.log.debug("_rm_device circus client call")
        except CircusException:
            self.log.debug("Could not rm process: %s", name, exc_info=self.debug)


    def run_forever(self, sleep_interval):
        """Runs startstop_once every sleep_interval - Should be used only if this is the only managed process"""
        while 1:
            self.startstop_once()
            time.sleep(sleep_interval)
