import logging
from circus.client import CircusClient
from circus.exc import CallError
from circus.util import DEFAULT_ENDPOINT_DEALER

LOG = logging.getLogger("brewpi-spawner")
LOG.setLevel(logging.INFO)

class CircusException(Exception):
    """Raised from FTCircusHandler"""
    pass


class CircusMgr(object):
    """Fermentrack Circus Handler, It is a simple wrapper around
    circus client, any errors raised as CircusException"""

    def __init__(self, connection_timeout=2, circus_endpoint=DEFAULT_ENDPOINT_DEALER):
        self._client = CircusClient(
            timeout=connection_timeout, endpoint=circus_endpoint)

    def _call(self, command, **props):
        message = {"command": command, "properties": props or {}}
        try:
            res = self._client.call(message)
        except CallError, callerr:
            LOG.debug("Error from circus", exc_info=True)
            raise CircusException("Could send message to circus: {}".format(callerr))
        if res['status'] == u'error':
            raise CircusException("Error: {}".format(res['reason']))
        return res

    def signal(self, name, signal=9):
        """Send signal to process, signal defaults to 9 (SIGTERM)"""
        self._call("signal", name=name, signal=signal)

    def reload(self, name, waiting=False, graceful=True, sequential=False):
        """Reload the arbiter/watcher

        If ``waiting`` is False (default), the call will return immediately
        after calling ``reload`` process.
        """
        response = self._call(
            "reload", name=name, graceful=graceful,
            sequential=sequential, waiting=waiting
        )
        return True if response['status'] == u'ok' else False

    def start(self, name, waiting=False):
        """Start circus process that has been stopped

        If ``waiting`` is False (default), the call will return immediately
        after calling ``start`` process.
        """
        response = self._call("start", name=name, waiting=waiting)
        return True if response['status'] == u'ok' else False

    def restart(self, name=None):
        """Restart a or all circus process(es)

        If ``name`` is None all processes under circus will be restarted
        """
        if name:
            response = self._call("restart", name=name)
        else:
            response = self._call("restart")
        return True if response['status'] == u'ok' else False

    def stop(self, name, waiting=False):
        """Stop a circus process, like suspend, the processess is stopped but still
        in circus, to resume use ``start``

        If ``waiting`` is False (default), the call will return immediately
        after calling ``stop`` process.
        """
        response = self._call("stop", name=name, waiting=waiting)
        return True if response['status'] == u'ok' else False

    def add_controller(self, cmd, name, logpath):
        """Add a new brewpi controller script"""
        response = self._call(
            "add",
            cmd=cmd,
            name=name,
            start=True,
            options={
                "copy_env": True,
                "stdout_stream": {
                    "class": "FileStream",
                    "filename": u"%s/%s-stdout.log" % (logpath, name),
                },
                "stderr_stream": {
                    "class": "FileStream",
                    "filename": u"%s/%s-stderr.log" % (logpath, name),
                }

            }
        )
        return response

    def remove(self, name):
        """Stop and Remove ``name`` from circus fully"""
        response = self._call("rm", name=name)
        return response

    def get_applications(self, verbose=False):
        """Get currently running processes

        If ``verbose`` is False a simple list will be returned
        if True circus information will be included.
        """
        response = self._call("list")
        if verbose:
            return response
        return response.get("watchers")

    def application_status(self, name, verbose=False):
        """Get process status

        If ``verbose`` is False it will return status, or "not running"
        if True circus information will be included.
        """
        response = self._call("status", name=name)
        if verbose:
            return response
        return str(response['status']) if response['status'] != u'error' else 'not running'

    def quit_circus(self):
        """quit_circus will quit the circus daemon, and need to be started again
        by some other means
        """
        response = self._call("quit")
        return response


if __name__ == '__main__':
    import time
    fc = CircusMgr()
    #print fc.get_applications()
    print fc.stop("fermentrack")
    print fc.application_status("fermentrack")
    time.sleep(2)
    print fc.get_applications()
    print fc.application_status("fermentrack")
    print fc.start("fermentrack")
    print fc.application_status("fermentrack")
    print fc.application_status("fermentrack1111")
    # print fc.quit_circus()
