Installing Fermentrack
========================

There are three main ways to install Fermentrack:

* One-line fully automated
* Semi-automated
* Manual

Regardless of what method you choose, all of these expect that your Raspberry Pi has been properly set up with a working
copy of Raspbian. If Raspbian is not yet installed, please read and complete :doc:`Raspi Setup`

Fully Automated - `[Video] <https://youtu.be/9hRH1dNygnk>`__
--------------------------------------------------------------

The easiest way to install Fermentrack is via a single command executed on your Raspberry Pi. To install via this method, simply SSH into your Raspberry Pi and execute:

``curl -L install.fermentrack.com | sudo bash``

Follow the prompts as needed, and once the script completes, you're done!


Semi-Automated
-----------------

If you prefer a slightly less automatic installation method, you can download the fermentrack-tools repo from git and use the install script contained therein. To install using this script, do the following:

1. Log into your Raspberry Pi
2. install ``git`` (Type ``sudo apt-install git-core``)
3. Clone the repo (``git clone https://github.com/thorrak/fermentrack-tools.git``)
4. Run the install script (``sudo fermentrack-tools/install.sh``)
5. Follow the prompts on screen. Relaunch the install script if prompted.
6. Once installation completes, open a web browser and connect to Fermentrack to complete the installation process.



Manual
-------

Unfortunately, the manual installation instructions haven't been fully written yet. That said, below is a general overview of what needs
to happen. The steps below need to be run in order - from top to bottom. The command to run is in the right column, with a
brief description of what the command seeks to accomplish in the left.

.. todo:: Add callout for version number here


.. list-table::
    :header-rows: 1

    * - Log into your Raspberry Pi via SSH or pull up a terminal window
      -
    * - Set the current user to `root`
      - ``sudo su``
    * - Update your apt package list
      - ``apt-get update``
    * - Upgrade all already installed packages via apt
      - ``apt-get upgrade``
    * - Install the system-wide packages (nginx, etc.)
      - ``apt-get install -y git-core build-essential nginx redis-server avrdude bluez libcap2-bin libbluetooth3 python3-venv python3-dev python3-zmq python3-scipy python3-numpy``
    * - Add the fermentrack user
      - ``useradd -m -G dialout fermentrack -s /bin/bash``
    * - Disable the fermentrack user's password
      - ``passwd -d fermentrack``
    * - Add the fermentrack user to the www-data group
      - ``usermod -a -G www-data fermentrack``
    * - Clone the Fermentrack repo
      - ``sudo -u fermentrack -H git clone https://github.com/thorrak/fermentrack.git "/home/fermentrack/fermentrack"``
    * - Create the virtualenv for launching fermentrack
      - ``sudo -u fermentrack -H git clone https://github.com/thorrak/fermentrack.git "/home/fermentrack/fermentrack"``
    * - Manually link numpy into the virtualenv
      - ``sudo -u fermentrack -H git clone https://github.com/thorrak/fermentrack.git "/home/fermentrack/fermentrack"``
    * - Manually link scipy into the virtualenv
      - ``sudo -u fermentrack -H git clone https://github.com/thorrak/fermentrack.git "/home/fermentrack/fermentrack"``
    * - Enable Python to interact with bluetooth
      - (See appropriate section below for instructions)

    * - Change to the utils directory
      - ``cd /home/fermentrack/fermentrack/utils/``
    * - Create the secretsettings.py file
      - ``sudo -u fermentrack -H bash "$installPath"/fermentrack/utils/make_secretsettings.sh``
    * - Run the Fermentrack upgrade script
      - ``sudo -u fermentrack -H bash /home/fermentrack/fermentrack/utils/upgrade3.sh``

    * - Set up Nginx
      - (See appropriate section below for instructions)

    * - Create the cron entries to launch Circus/Fermentrack
      - ``sudo -u fermentrack -H bash /home/fermentrack/fermentrack/utils/updateCronCircus.sh add2cron``
    * - Launch Circus/Fermentrack
      - ``sudo -u fermentrack -H bash /home/fermentrack/fermentrack/utils/updateCronCircus.sh start``



Enabling Python to Interact with Bluetooth
-----------------------------------------------

  PYTHON3_INTERPRETER="$(readlink -e $installPath/venv/bin/python)"
  if [ -a ${PYTHON3_INTERPRETER} ]; then
    sudo setcap cap_net_raw+eip "$PYTHON3_INTERPRETER"


Setting Up Nginx
------------------

Although Fermentrack may be installed, without Nginx being configured, the app will not be accessible via a web browser.


The default-fermentrack configuration file can be found at: `fermentrack-tools/nginx-configs/default-fermentrack <https://raw.githubusercontent.com/thorrak/fermentrack-tools/master/nginx-configs/default-fermentrack) as an example>`__.
You will need to find and replace all instances of "brewpiuser" with "fermentrack".

.. todo:: Rewrite this section

::

  rm -f /etc/nginx/sites-available/default-fermentrack &> /dev/null
  # Replace all instances of 'brewpiuser' with the fermentrackUser we set and save as the nginx configuration
  sed "s/brewpiuser/${fermentrackUser}/" "$myPath"/nginx-configs/default-fermentrack > /etc/nginx/sites-available/default-fermentrack
  rm -f /etc/nginx/sites-enabled/default &> /dev/null
  ln -sf /etc/nginx/sites-available/default-fermentrack /etc/nginx/sites-enabled/default-fermentrack
  service nginx restart

