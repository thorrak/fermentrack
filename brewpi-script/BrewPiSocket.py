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

import sys
import socket
import os
import BrewPiUtil as util

class BrewPiSocket:
	"""
	A wrapper class for the standard socket class.
	"""

	def __init__(self, cfg):
		""" Creates a BrewPi socket object and reads the settings from a BrewPi ConfigObj.
		Does not create a socket, just prepares the settings.

		Args:
		cfg: a ConfigObj object form a BrewPi config file
		"""

		self.type = 'f'  # default to file socket
		self.file = None
		self.host = 'localhost'
		self.port = None
		self.sock = 0

		isWindows = sys.platform.startswith('win')
		useInternetSocket = bool(cfg.get('useInetSocket', isWindows))
		if useInternetSocket:
			self.port = int(cfg.get('socketPort', 6332))
			self.host = cfg.get('socketHost', "localhost")
			self.type = 'i'
		else:
			self.file = util.addSlash(cfg['scriptPath']) + 'BEERSOCKET'

	def __repr__(self):
		"""
		This special function ensures BrewPiSocket is printed as a dict of its member variables in print statements.
		"""
		return repr(self.__dict__)

	def create(self):
		""" Creates a socket socket based on the settings in the member variables and assigns it to self.sock
		This function deletes old sockets for file sockets, so do not use it to connect to a socket that is in use.
		"""
		if self.type == 'i':  # Internet socket
			self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			self.sock.bind((self.host, self.port))
			util.logMessage('Bound to TCP socket on port %d ' % self.port)
		else:
			if os.path.exists(self.file):
				# if socket already exists, remove it. This prevents  errors when the socket is corrupt after a crash.
				os.remove(self.file)
			self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
			self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			self.sock.bind(self.file)  # Bind BEERSOCKET
			# set all permissions for socket
			os.chmod(self.file, 0777)

	def connect(self):
		"""	Connect to the socket represented by BrewPiSocket. Returns a new connected socket object.
		This function should be called when the socket is created by a different instance of brewpi.
		"""
		sock = socket.socket
		try:
			if self.type == 'i':  # Internet socket
				sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
				util.logMessage('Bound to existing TCP socket on port %d ' % self.port)
				sock.connect((self.host, self.port))
			else:
				sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
				sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
				sock.connect(self.file)
		except socket.error as e:
			print e
			sock = False
		finally:
			return sock

	def listen(self):
		"""
		Start listing on the socket, with default settings for blocking/backlog/timeout
		"""
		self.sock.setblocking(1)  # set socket functions to be blocking
		self.sock.listen(10)  # Create a backlog queue for up to 10 connections
		self.sock.settimeout(0.1)  # set to block 0.1 seconds, for instance for reading from the socket

	def read(self):
		"""
		Accept a connection from the socket and reads the incoming message.

		Returns:
		conn: socket object when an incoming connection is accepted, otherwise returns False
		msgType: the type of the message received on the socket
		msg: the message body
		"""
		conn = False
		msgType = ""
		msg = ""
		try:
			conn, addr = self.sock.accept()
			message = conn.recv(4096)
			if "=" in message:
				msgType, msg = message.split("=", 1)
			else:
				msgType = message
		except socket.timeout:
			conn = False
		finally:
			return conn, msgType, msg

