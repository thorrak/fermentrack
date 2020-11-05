# wraps a tcp socket stream in a object that looks like a serial port
# this allows seemless integration with exsiting brewpi-script code
from __future__ import print_function

import socket, errno
from . import mdnsLocator
import os, sys, time


# Copying this in from BrewPiUtil to prevent chained imports
def printStdErr(*objs):
    print("", *objs, file=sys.stderr)

def logMessage(message):
    """
    Prints a timestamped message to stderr
    """
    printStdErr(time.strftime("%b %d %Y %H:%M:%S   ") + message)

class TCPSerial(object):
    def __init__(self, host=None, port=None, hostname=None):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # find BrewPi's via mdns lookup
        self.host=host
        self.port=port
        self.retries=10 # max reconnect attempts to try when doing a read or write operation
        self.retryCount=0 # count of reconnect attempts performed
        if hostname:
            if host is None:
                logMessage("Unable to resolve hostname {}. Exiting.".format(hostname))
                exit(1)
            else:
                logMessage("Connecting to BrewPi " + hostname + " (via " + host + ") on port " + str(port))
        else:
            logMessage("Connecting to BrewPi " + host + " on port " + str(port))
        self.open()
        self.setTimeout(0.5)
        # self.timeout=self.sock.gettimeout()
        self.name=host + ':' + str(port)
        return      
        
    def flushInput(self):
        # this has no meaning to tcp
        return
    
    def flushOutput(self):
        #Clear output buffer, aborting the current output and discarding all that is in the buffer.
        # this has no meaning to tcp
        return

    def read(self, size=1):
        #Returns:    Bytes read from the port.
        #Read size bytes_read from the serial port. If a timeout is set it may return less characters as requested. With no timeout it will block until the requested number of bytes_read is read.
        bytes_read=None
        try: 
            bytes_read=self.sock.recv(size)
        except socket.timeout: # timeout on receive just means there is nothing in the buffer.  This is not an error
            return None
        except socket.error: # other socket errors probably mean we lost our connection.  try to recover it.
            bytes_read = b''
        # Because an empty buffer returns socket.timeout, bytes_read being none or a blank bytestring means that we're
        # disconnected. Print a message & attempt to reconnect
        if bytes_read is None or bytes_read == b'':
            logMessage("Lost connection to controller on read. Attempting to reconnect.")
            self.close()
            self.open()
            # TODO - add another "read" here

        if hasattr(bytes_read, 'decode'):
            return bytes_read.decode(encoding="cp437")
        else:
            return bytes_read

    def readline(self, size=None, eol='\n'):
        #Parameters:    
        #Read a line which is terminated with end-of-line (eol) character (\n by default) or until timeout.
        buf=self.read(1)
        line=buf
        while buf is not None and buf!='\n':
            buf=self.read(1)
            if buf is not None and buf!='\n':
                line+=buf
        return line
            
   
    def write(self, data):
        #Returns:    Number of bytes written.
        #Raises SerialTimeoutException:
        #     In case a write timeout is configured for the port and the time is exceeded.
        #Write the string data to the port.
        try:
            if hasattr(data, 'encode'):
                # This feels so wrong...
                bytes_data = data.encode(encoding="cp437")
            else:
                bytes_data = data
            bytes_returned=self.sock.sendall(bytes_data)
        except socket.timeout: # A write timeout is probably a connection issue
            logMessage("Lost connection to controller on write. Attempting to reconnect.")
            self.close()
            self.open()
            bytes_returned=self.write(data)
        except socket.error: # general errors are most likely to be a timeout disconnect from BrewPi, so try to recover.
            logMessage("Lost connection to controller on write. Attempting to reconnect.")
            self.close()
            self.open()
            bytes_returned=self.write(data)

        return len(data)
    
    def inWaiting(self):
        #Return the number of chars in the receive buffer.
        # Note: the value returned by inWaiting should be greater than the send buffer size on BrewPi firmware
        # If not, brewpi.py may not grab the next whole buffered message.
        return 4096  #tcp socket doesnt give us a way to know how much is in the buffer, so we assume there is always something

    def setTimeout(self, value=0.1):
        if value:
            self.sock.settimeout(value)
            self.timeout=self.sock.gettimeout()
        return self.sock.gettimeout()
    
    def flush(self):
        # Flush of file like objects. In this case, wait until all data is written.
        # This has no meaning for TCP
        return

    def close(self):
        # Shutdown, then close port
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        except OSError as exc:
            if exc.errno == errno.ENOTCONN:
                pass  # Socket is not connected, so can't send FIN packet.
            else:
                raise
        return self.sock.close()

    def isOpen(self):
        if self.sock:
            return True
        else:
            return False

    def open(self):
        mdnsLocator.locate_brewpi_services()  # This causes all the BrewPi devices to resend their mDNS info

        connected = False

        # TODO - Debug this. Currently, reconnection doesn't actually work.
        while self.retryCount < self.retries:
            try:
                self.sock.connect((self.host, self.port))
                connected = True
                break
            except (socket.gaierror) as e:
                self.retryCount += 1
                # time.sleep(1)
            except (socket.error) as e:  # Catches "bad file descriptor" error
                self.retryCount += 1
                # time.sleep(1)

        if connected:
            logMessage("Successfully connected to controller.")
            self.retryCount = 0
        else:
            logMessage("Unable to connect to BrewPi " + self.host + " on port " + str(self.port) + ". Exiting.")
            sys.exit(1)


