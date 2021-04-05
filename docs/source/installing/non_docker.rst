Installing Fermentrack without Docker
=====================================

The use of Docker is recommended for all Fermentrack installations that are not being used for active development, as
Docker ensures a consistent environment and simple upgrades.

There are two main ways to install Fermentrack without Docker:

* Semi-automated
* Manual

Regardless of what method you choose, all of these expect your Raspberry Pi to be adequately set up with a working
copy of Raspbian. If you have not yet installed Raspbian please read and complete :doc:`Raspi_Setup`

.. warning:: The overwhelming number of issues with Fermentrack are caused by environmental problems Docker helps prevent.


Semi-Automated
-----------------

The easiest way to install without Docker is to run the legacy non-docker install script. To do this, simply complete
the following:

1. Log into your Raspberry Pi
2. install ``git`` (Type ``sudo apt-install git-core``)
3. Clone the repo (``git clone https://github.com/thorrak/fermentrack-tools.git``)
4. Run the install script (``sudo fermentrack-tools/non_docker_install/install.sh``)
5. Follow the prompts on screen. Relaunch the install script if prompted.
6. Once installation completes, open a web browser and connect to Fermentrack to complete the installation process.


This script will:

- Install the software/packages necessary for Fermentrack to run
- Install Fermentrack
- Install Nginx
- Set up Nginx to access Fermentrack


Manual
-------

If you want to install Fermentrack manually, simply open the ``non_docker_install/install.sh`` script from
the `fermentrack-tools`_ repo and follow the commands in the order they are executed by the script.

.. note:: Many of these commands require being executed as ``sudo`` to work.
