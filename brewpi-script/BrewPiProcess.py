# NOTE - This file is no longer used and can likely be deleted. Once refactoring of updateFirmware.py is complete,
# delete this.

# TODO - Delete this file once refactoring of updateFirmware.py is complete

# Copyright 2013 BrewPi
# This file is part of BrewPi.

# BrewPi is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# BrewPi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with BrewPi.  If not, see <http://www.gnu.org/licenses/>.


import pprint
import os
import sys
from time import sleep
from distutils.version import LooseVersion

# TODO - Delete the below items if we don't need it as a result of everything being loaded in brewpi.py
# # Load up the Django specific stuff
# BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# proj_path = os.path.join(BASE_DIR, '..')
# sys.path.append(proj_path)

import app.models as models  # This SHOULD work due to the sys.path.append above.


try:
    import psutil
    if LooseVersion(psutil.__version__) < LooseVersion("2.0"):
        print >> sys.stderr, "Your version of pstuil is %s \n" \
        "BrewPi requires psutil 2.0 or higher, please upgrade your version of psutil.\n" \
        "This can best be done via pip, please run:\n" \
        "  sudo apt-get install build-essential python-dev python-pip\n" \
        "  sudo pip install psutil --upgrade\n" % psutil.__version__
        sys.exit(1)


except ImportError:
    print "BrewPi requires psutil to run, please install it via pip: 'sudo pip install psutil --upgrade"
    sys.exit(1)

import BrewPiSocket
import BrewPiUtil as util


class BrewPiProcess:
    """
    This class represents a running BrewPi process.
    It allows other instances of BrewPi to see if there would be conflicts between them.
    It can also use the socket to send a quit signal or the pid to kill the other instance.
    """
    def __init__(self):
        self.pid = None  # pid of process
        self.cfg = None  # config file of process, full path
        self.port = None  # serial port the process is connected to
        self.sock = None  # BrewPiSocket object which the process is connected to

    def as_dict(self):
        """
        Returns: member variables as a dictionary
        """
        return self.__dict__

    def quit(self):
        """
        Sends a friendly quit message to this BrewPi process over its socket to aks the process to exit.
        """
        if self.sock is not None:
            conn = self.sock.connect()
            if conn:
                conn.send('quit')
                conn.close()  # do not shutdown the socket, other processes are still connected to it.
                print "Quit message sent to BrewPi instance with pid %s!" % self.pid
                return True
            else:
                print "Could not connect to socket of BrewPi process, maybe it just started and is not listening yet."
                print "Could not send quit message to BrewPi instance with pid %d!" % self.pid
                print "Killing it instead!"
                self.kill()
                return False

    def kill(self):
        """
        Kills this BrewPiProcess with force, use when quit fails.
        """
        process = psutil.Process(self.pid)  # get psutil process my pid
        try:
            process.kill()
            print "SIGKILL sent to BrewPi instance with pid %d!" % self.pid
        except psutil.AccessDenied:
            print >> sys.stderr, "Cannot kill process %d, you need root permission to do that." % self.pid
            print >> sys.stderr, "Is the process running under the same user?"

    def conflict(self, otherProcess):
        if self.pid == otherProcess.pid:
            return 0  # this is me! I don't have a conflict with myself
        # TODO - Test this to make sure that it works with the database configuration. May already work.
        if otherProcess.cfg == self.cfg:
            print "Conflict: same config file as another BrewPi instance already running."
            return 1
        if otherProcess.port == self.port:
            print "Conflict: same serial port as another BrewPi instance already running."
            return 1
        if [otherProcess.sock.type, otherProcess.sock.file, otherProcess.sock.host, otherProcess.sock.port] == \
                [self.sock.type, self.sock.file, self.sock.host, self.sock.port]:
            print "Conflict: same socket as another BrewPi instance already running."
            return 1
        return 0


class BrewPiProcesses():
    """
    This class can get all running BrewPi instances on the system as a list of BrewPiProcess objects.
    """
    def __init__(self):
        self.list = []

    def update(self):
        """
        Update the list of BrewPi processes by receiving them from the system with psutil.
        Returns: list of BrewPiProcess objects
        """
        bpList = []
        matching = []

        # some OS's (OS X) do not allow processes to read info from other processes. 
        try:
            matching = [p for p in psutil.process_iter() if any('python' in p.name() and 'brewpi.py'in s for s in p.cmdline())]
        except psutil.AccessDenied:
            pass
        except psutil.ZombieProcess:
            pass

        for p in matching:
            bp = self.parseProcess(p)
            if bp:
                bpList.append(bp)
        self.list = bpList
        return self.list

    def parseProcess(self, process):
        """
        Converts a psutil process into a BrewPiProcess object by parsing the config file it has been called with.
        Params: a psutil.Process object
        Returns: BrewPiProcess object
        """
        bp = BrewPiProcess()
        db_config = None
        cfg = None
        try:
            bp.pid = process._pid
            try:  # If this is a database configured installation, try loading via the process ID
                db_config = models.BrewPiDevice.objects.get(process_id=bp.pid)
            except:
                cfg = [s for s in process.cmdline() if '.cfg' in s]  # get config file argument
        except psutil.NoSuchProcess:
            # process no longer exists
            return None
        if db_config is not None:  # If this is a database-configured installation, use the database configuration
            bp.cfg = util.read_config_from_database_without_defaults(db_config)
        else:
            if cfg:
                cfg = cfg[0]  # add full path to config file
            else:
                # use default config file location
                cfg = util.scriptPath() + "/settings/config.cfg"
            bp.cfg = util.read_config_file_with_defaults(cfg)

        bp.port = bp.cfg['port']
        bp.sock = BrewPiSocket.BrewPiSocket(bp.cfg)
        return bp

    def get(self):
        """
        Returns a non-updated list of BrewPiProcess objects
        """
        return self.list

    def me(self):
        """
        Get a BrewPiProcess object of the process this function is called from
        """
        myPid = os.getpid()
        myProcess = psutil.Process(myPid)
        return self.parseProcess(myProcess)

    def findConflicts(self, process):
        """
        Finds out if the process given as argument will conflict with other running instances of BrewPi
        Always returns a conflict if a firmware update is running

        Params:
        process: a BrewPiProcess object that will be compared with other running instances

        Returns:
        bool: True means there are conflicts, False means no conflict
        """

                # some OS's (OS X) do not allow processes to read info from other processes.
        matching = []
        try:
            matching = [p for p in psutil.process_iter() if any('python' in p.name() and 'flashDfu.py'in s for s in p.cmdline())]
        except psutil.AccessDenied:
            pass
        except psutil.ZombieProcess:
            pass

        if len(matching) > 0:
            return 1

        try:
            matching = [p for p in psutil.process_iter() if any('python' in p.name() and 'updateFirmware.py'in s for s in p.cmdline())]
        except psutil.AccessDenied:
            pass
        except psutil.ZombieProcess:
            pass


        if len(matching) > 0:
            return 1

        for p in self.list:
            if process.pid == p.pid:  # skip the process itself
                continue
            elif process.conflict(p):
                return 1
        return 0

    def as_dict(self):
        """
        Returns the list of BrewPiProcesses as a list of dicts, except for the process calling this function
        """
        outputList = []
        myPid = os.getpid()
        self.update()
        for p in self.list:
            if p.pid == myPid:  # do not send quit message to myself
                continue
            outputList.append(p.as_dict())
        return outputList

    def __repr__(self):
        """
        Print BrewPiProcesses as a dict when passed to a print statement
        """
        return repr(self.as_dict())

    def quitAll(self):
        """
        Ask all running BrewPi processes to exit
        """
        myPid = os.getpid()
        self.update()
        for p in self.list:
            if p.pid == myPid:  # do not send quit message to myself
                continue
            else:
                p.quit()

    def stopAll(self, dontRunFilePath):
        """
        Ask all running Brewpi processes to exit, and prevent restarting by writing
        the do_not_run file
        """
        if not os.path.exists(dontRunFilePath):
            # if do not run file does not exist, create it
            dontrunfile = open(dontRunFilePath, "w")
            dontrunfile.write("1")
            dontrunfile.close()
        myPid = os.getpid()
        self.update()
        for p in self.list:
            if p.pid == myPid:  # do not send quit message to myself
                continue
            else:
                p.quit()

    def killAll(self):
        """
        Kill all running BrewPi processes with force by sending a sigkill signal.
        """
        myPid = os.getpid()
        self.update()
        for p in self.list:
            if p.pid == myPid:  # do not commit suicide
                continue
            else:
                p.kill()


def testKillAll():
    """
    Test function that prints the process list, sends a kill signal to all processes and prints the updated list again.
    """
    allScripts = BrewPiProcesses()
    allScripts.update()
    print ("Running instances of BrewPi before killing them:")
    pprint.pprint(allScripts)
    allScripts.killAll()
    allScripts.update()
    print ("Running instances of BrewPi before after them:")
    pprint.pprint(allScripts)


def testQuitAll():
    """
    Test function that prints the process list, sends a quit signal to all processes and prints the updated list again.
    """
    allScripts = BrewPiProcesses()
    allScripts.update()
    print ("Running instances of BrewPi before asking them to quit:")
    pprint.pprint(allScripts)
    allScripts.quitAll()
    sleep(2)
    allScripts.update()
    print ("Running instances of BrewPi after asking them to quit:")
    pprint.pprint(allScripts)
