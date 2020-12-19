.. include:: ../global.rst

Coexistence with Other Apps
====================================================

Unlike apps such as RaspberryPints and BrewPi-www, which use `Apache <https://www.apache.org/>`_ to directly serve
webpages, Fermentrack uses `Nginx <https://nginx.org/en/>`_ as a reverse proxy to pass connections to the Fermentrack
application running on your Pi. Fermentrack can coexist peacefully with other apps - including those that use Apache -
but some additional configuration will be required.


.. note:: This document assumes that your installation of Fermentrack is running inside Docker


Port Utilization
-------------------------------

For Docker-based installations, port utilization is the primary issue preventing coexistence with other apps.
Fermentrack uses several, all of which must be free for the installation to be successful. The most likely
of these ports to be occupied - port 80 - can be changed at the time of installation by running the installation
script manually (see below).

- 80 - **Configurable** - The primary port through which Fermentrack is accessed
- 5432 - Used by Postgres
- 6379 - Used by Redis
- 7555 - The socket through which the Fermentrack app is directly accessed
- 7556 - Used by Circus
- 7557 - Used by Circus

BrewPi-script instances may use additional ports not listed above  - these are configurable through the Fermentrack
interface.


Changing Fermentrack away from Port 80
--------------------------------------

Port 80 is the standard port for most web applications - including Fermentrack - which also causes it to be the most
likely to have conflicts with other applications. If you need to change the port Fermentrack is accessible through this
can be accomplished by re-running the install.sh script included with `fermentrack-tools`_.

1. Log into your Raspberry Pi via ``ssh``
2. Change to the ``fermentrack-tools`` directory
3. Run ``./install.sh``
4. When prompted, select a port other than 80.
