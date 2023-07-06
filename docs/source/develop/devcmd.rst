.. include:: ../global.rst

Useful development commands
===========================

Activate the virtual python environment
---------------------------------------

To interact with the fermentrack installation from the terminal you need to activate the virtual python environment. 

* ``cd ~/fermentrack``
* ``source .env/bin/activate``

If you are running this on a normal install the virtual enviroment is activated this way

* ``cd ~/fermentrack``
* ``source ../venv/bin/activate``

Interacting with circus
-----------------------

Fermentrack uses circus to control the various parts of the program [Require activated python environment]. 

* ``circusctl status``
* ``circusctl stop``
* ``circusctl start``

These commands can be used to start/stop parts of the installation which will be running by default when the VM starts.

Keeping your fork up to date with thorrak/fermentrack
-----------------------------------------------------

First we need to add the thorrak repository as an upstream repo (you only need to do this once)

* ``cd ~/fermentrack``
* ``git remote add upstream git@github.com:thorrak/fermentrack.git``

When you want to sync you run the following commands:

* ``cd ~/fermentrack``
* ``git fetch upstream``
* ``git checkout master``
* ``git merge upstream/master``
* ``git push``

