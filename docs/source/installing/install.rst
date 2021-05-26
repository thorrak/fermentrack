Installing Fermentrack
========================

Fermentrack is intended to be installed as a Docker container as part of a Docker compose stack. There are three main
ways to install Fermentrack:

* One-line fully automated
* Semi-automated
* Manual

Regardless of what method you choose, all of these expect that your Raspberry Pi has been properly set up with a working
copy of Raspbian. If Raspbian is not yet installed, please read and complete :doc:`Raspi_Setup`

Fully Automated
-----------------

The easiest way to install Fermentrack is via a single command executed on your Raspberry Pi. To install via this
method, simply SSH into your Raspberry Pi and execute:

``curl -L install.fermentrack.com | sudo bash``

Follow the prompts as needed, and once the script completes, you're done!

You can also watch a video of this process on YouTube at: XXXX

.. todo:: Come back and re-add the video link once the video of the docker install is available.


Semi-Automated
-----------------

If you prefer a slightly less automatic installation method, you can download the `fermentrack-tools`_ repo from git and
use the install script contained therein. To install using this script, do the following:

1. Log into your Raspberry Pi
2. install ``git`` (Type ``sudo apt-install git-core``)
3. Clone the repo (``git clone https://github.com/thorrak/fermentrack-tools.git``)
4. Run the install script (``cd fermentrack-tools && sudo install.sh``)
5. Follow the prompts on screen. Relaunch the install script if prompted.
6. Once installation completes, open a web browser and connect to Fermentrack to complete the installation process.



Manual
-------

If you want to install Fermentrack manually, simply open the ``install.sh`` script from
the `fermentrack-tools`_ repo and follow the commands in the order they are executed by the script.
