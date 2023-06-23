brewpi-script-daemon
====================

BrewPi-Script-Daemon is a process daemon for managing BrewPi-Script instances. It was initially designed for Fermentrack, in order to replace the use of Circus. 

BrewPi-Script-Daemon consists of two components:

* BrewPi-Script - The script which interfaces between a web interface (e.g. Fermentrack) and BrewPi controllers running BrewPi firmware. BrewPi-Script was originally created by Elco as part of the [BrewPi project](https://github.com/BrewPi/brewpi-script). Modifications have been made by Thorrak to enable daemonization.
* Process daemon - The daemon which monitors for calls to create BrewPi-Script instances and spawns/manages them.


Licensing
-------
BrewPi-Script is licensed under the **GPL v3**, a copy of which is included in LICENSE.md. 

The process daemons and other code *not* part of BrewPi-Script are licensed under MIT.

These licenses may differ from that used for other associated projects, including the BrewPi firmware, BrewPi-www, Fermentrack, etc.
