# Fermentrack

[![Fermentrack Logo](http://www.fermentrack.com/static/img/fermentrack_logo.png "Fermentrack")](http://www.fermentrack.com/)

[![Documentation Status](https://readthedocs.org/projects/fermentrack/badge/?version=master)](http://fermentrack.readthedocs.io/en/master/?badge=master)
                
#### A replacement web interface for BrewPi

Fermentrack is a complete replacement for the web interface used by BrewPi written in Python using the Django web framework. It adds key features such as the ability to manage multiple controllers and control both Arduino-based and ESP8266-based controllers connecting via serial or WiFi. Fermentrack also integrates standalone support for Tilt & iSpindel specific gravity sensors allowing specific gravity to be tracked in the absence of BrewPi controllers.

Fermentrack is Python-based, does not require PHP5, and works with Raspbian Stretch or later including on Raspberry Pi 3 B+. Fermentrack is intended to be installed on a fresh installation of Raspbian and will conflict with brewpi-www if installed on the same device. 

Want to see it in action? See videos of key Fermentrack features on [YouTube](https://www.youtube.com/playlist?list=PLCs4FqrNRHd00wsfsP7cTs83e19S2-Atf)!


### Included with Fermentrack

* **Fermentrack** - The Django-based replacement for brewpi-www. Licensed under MIT license.
* **brewpi-script** - Installed alongside Fermentrack is brewpi-script. Licensed under GPL v3.
* **nginx** - A reverse proxy/webserver. Licensed under 2-Clause BSD-like license.
* **circusd** - A python-based process manager. Licensed under the Apache license, v2.0.
* **chaussette** - A wsgi server. 


## New Features

One of the key reasons to write Fermentrack was to incorporate features that are missing in the official BrewPi web interface. The following are just some of the features that have been added:

* Native multi-chamber support
* Cleaner, more intuitive controller setup
* Integrated support for ESP8266-based controllers
* Official support for "legacy" controllers
* Native support (including mDNS autodetection) for WiFi controllers
* Specific gravity sensor support, including Tilt Hydrometers & iSpindel devices


## Installation & Documentation

Full documentation for Fermentrack (including complete installation instructions) is available at [https://docs.fermentrack.com/](https://docs.fermentrack.com/).


### Quick Installation Instructions

1. Set up your Raspberry Pi (Install Raspbian, enable SSH)
2. Log into your Raspberry Pi via the terminal or SSH and run `curl -L install.fermentrack.com | sudo bash`
3. Wait for the installation to complete (can take ~45 mins) and log into Fermentrack 


## Requirements

* Raspberry Pi Zero, 2 B, or 3 /w Internet Connection
* Fresh Raspbian install (Stretch or later preferred, Jessie supported)
* 1GB of free space available

**PLEASE NOTE** - Fermentrack is currently intended to be installed on a fresh installation of Raspbian. It is **not** intended to be installed alongside brewpi-www and will conflict with the apache server brewpi-www installs. 

