# Installing Fermentrack

There are three main ways to install Fermentrack - One-line fully automated, semi-automated, and manual.

Regardless of what method you choose, all of these expect that your Raspberry Pi has been properly set up with a working copy of Raspbian. 

## Fully Automated - [Video]()

The easiest way to install Fermentrack is via a single command executed on your Raspberry Pi. To install via this method, simply SSH into your Raspberry Pi and execute:

`curl -L install.fermentrack.com | sudo bash`

Follow the prompts as needed, and once the script completes, you're done! 


## Semi-Automated

If you prefer a slightly less automatic installation method, you can download the fermentrack-tools repo from git and use the install script contained therein. To install using this script, do the following:

1. Log into your Raspberry Pi
1. install `git` (Type `sudo apt-install git-core`)
1. Clone the repo (`git clone https://github.com/thorrak/fermentrack-tools.git`)
1. Run the install script (`sudo fermentrack-tools/install.sh`)
1. Follow the prompts on screen. Relaunch the install script if prompted.
1. Once installation completes, open a web browser and connect to Fermentrack to complete the installation process.


## Manual

If you are interested in installing Fermentrack by hand, please refer to the manual installation instructions located [here](manual.md). 