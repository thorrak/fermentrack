.. include:: ../global.rst

Setting up a development environment based on Linux
===================================================

You dont need to be an expert in linux in order to use this setup. 

This guide will show you how to setup a fresh development environment for Fermentrack based on a virtual machine, Ubuntu (Linux) and Visual Studio Code. 
All of the tools are free for non commercial use.

Step 1 - Create a virtual machine
---------------------------------

I would recommend that you use a virtual machine for the development since this way you can keep a clean installation that is not 
impacted by any other installations.

There are several options for running a virtual machine, VMWare Player (Free for non commercial use) and VirtualBox to mention a few. 
In this guide we will use VMWare Player which should work on both Windows and MacOS.

* Download VMware Player and install (www.vmware.com)
* Download latest version of Ubuntu LTS (www.ubuntu.com)

**Ubuntu LTS release is required for Docker support when that development is done**

Create a virtual machine with the following miniumm configuration (should be the default options in Vmware)

* 20 Gb HD  
* 2 Gb RAM  
* 1 vCPU    

Select Ubuntu LTS image, enter username/password (**Use fermentrack as username**) and VMWare should automatically handle the installation for you.

During the first startup it will prompt for installation of updates, just accept these and wait for the installation to be 
done before proceding to the next step.

If you are using anything else than an US keyboard you will need to go into settings -> region & languages and add the correct keyboard setup.

Step 2 - Create a fork of the repository
----------------------------------------

To make changes to Fermentrack you need to create a Fork (copy) of the repository on Github. 

* Login or create an account on www.github.com
* Search for the fermentrack repository and create a fork

**It should show up under your repositories as <yourname>/fermentrack.**

Step 3 - Setting up development environment
-------------------------------------------

Step 3a - Install Visual Studio Code
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

First we need to install a code editor environment, I prefer Visualstudio Code which is a free IDE from Microsoft. 

* Open Ubuntu Software and search for "Visual Studio Code"

Step 3b - Install additional packages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The next part require us to type a few commands in a terminal window. So press the 9 dots in the lower left corner and search/start the program "Terminal".

Enter the following commands to install required packages:

* ``sudo apt install redis-server git gcc sqlitebrowser libbluetooth-dev bluez libcap2-bin avrdude``
* ``sudo apt install python3 python3-pip python3-dev python3-venv python3-zmq python3-scipy python3-numpy``

Step 3c - Setup SSH key with github
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In order to interact with your github repository the recommended way is to use SSH and for this to work you need to follow this guide on github;

https://docs.github.com/en/free-pro-team@latest/github/authenticating-to-github/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent

Step 3d - Create fork on github and make local clone
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once that is completed we can proceeed and make a clone of your fork (a clone is a local working copy of the repository)

* Navigate to your repository on github and press the green code button. 
* Select SSH and copy the link
* Navigate to your home directory and run the following commands

* ``cd ~``
* ``git clone git@github.com:<your repo>/fermentrack.git``

Step 3e - Create virtual python environment for fermentrack
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Next step is to create a virtual environment for python that is used to interact with the installation from the terminal. This will create a new virtual
environment under /home/fermentrack/.env and install the needed python packages. This will be automatically picked up by vscode later on.

* ``cd ~/fermentrack``
* ``python3 -m venv .env``
* ``source .env/bin/activate``
* ``pip3 install wheel``
* ``pip3 install -r requirements.txt``
* ``pip3 install numpy==1.18.4``

These commands will create the django secret, create/update the database to the latest version and add the circus demon.

* ``./utils/make_secretsettings.sh``
* ``python3 manage.py migrate``
* ``./utils/updateCronCircus.sh add2cron``

After these steps you should restart the virtual machine.

Step 3f - Create virtual python environment for doc generation [optional]
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This step will setup a python environment for creating a html version of the documentation stored under ~/fermentrack/docs

* ``cd ~/fermentrack/docs``
* ``python3 -m venv env``
* ``source env/bin/activate``
* ``pip3 install -r requirements.txt``

Now you can create the html documentation by running the command:

* ``cd ~/fermentrack/docs``
* ``make -B html``

Step 3g - Open project in VS Code and configure debugger
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Now you are ready to open the project in Visual Studio Code by starting the Code and opening the folder that contains the project, /home/fermentrack/fermentrack.

Open a file with the extension .py and VS code will prompt you to install a few add-ons for python.

Then select from the menu, RUN -> ADD CONFIGURATION -> Python -> Django. Paste the following configuration in that file.

.. code-block:: 

    {
        // Use IntelliSense to learn about possible attributes.
        // Hover to view descriptions of existing attributes.
        // For more information, visit: https://go.microsoft.com/fwlink/?linkid=830387
        "version": "0.2.0",
        "configurations": [
            {
                "name": "Python: Django",
                "type": "python",
                "request": "launch",
                "program": "${workspaceFolder}/manage.py",
                "args": [
                    "runserver",
                    "--noreload"
                ],
                "django": true
            },
            {
                "name": "Python: Huey",
                "type": "python",
                "request": "launch",
                "program": "${workspaceFolder}/manage.py",
                "args": [
                    "run_huey"
                ],
                "django": true
            }
        ]
    }	


This will create 2 run targets for the debugger that allows you to debug code.

* The first *runserver* will run the web server and allow debugging of the interface.
* The second *run_huey* will run the background task and allow for debugging of background tasks, such as external_push.

In the statusbar of VS Code select the correct python environment by clicking on the text "Python ..." and selecting the environment with the name .env (should be the last entry)

If you start the first entry the django application will be available on http://localhost:8000

