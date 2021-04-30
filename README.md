# Fermentrack

[![Fermentrack Logo](http://www.fermentrack.com/static/img/fermentrack_logo.png "Fermentrack")](http://www.fermentrack.com/)
[![FOSSA Status](https://app.fossa.com/api/projects/git%2Bgithub.com%2Fthorrak%2Ffermentrack.svg?type=shield)](https://app.fossa.com/projects/git%2Bgithub.com%2Fthorrak%2Ffermentrack?ref=badge_shield)

[![Documentation Status](https://readthedocs.org/projects/fermentrack/badge/?version=master)](http://fermentrack.readthedocs.io/en/master/?badge=master)
                
#### A replacement web interface for BrewPi

Fermentrack is an application designed to manage and log fermentation temperatures and specific gravity. It acts as a complete replacement for the web interface used by BrewPi written in Python using the Django web framework. It also can track Tilt Hydrometers and iSpindel specific gravity sensors - both alongside BrewPi controllers as well as by themselves.

Fermentrack is Python-based, does not require PHP5, and works with Raspbian Buster or later including on Raspberry Pi 3 B+. Fermentrack is intended to be installed on a fresh installation of Raspbian (or another Debian-based OS for x86/x64 installations) and will conflict with brewpi-www if installed on the same device. 

Want to see it in action? See videos of key Fermentrack features on [YouTube](https://www.youtube.com/playlist?list=PLCs4FqrNRHd00wsfsP7cTs83e19S2-Atf)!


### Included with Fermentrack

* **Fermentrack** - Django-based fermentation tracking and control interface. Replaces brewpi-www. Licensed under MIT license.
* **brewpi-script** - Installed alongside Fermentrack to control BrewPi controllers. Licensed under GPL v3.
* **nginx** - A reverse proxy/webserver. Licensed under 2-Clause BSD-like license.
* **circusd** - A python-based process manager. Licensed under the Apache license, v2.0.
* **chaussette** - A wsgi server. Licensed under the Apache license, v2.0.

## New Features

One of the key reasons to write Fermentrack was to incorporate features that are missing in the official BrewPi web interface. The following are just some of the features that have been added:

* Native multi-chamber support
* Cleaner, more intuitive controller setup
* Integrated support for ESP8266-based controllers
* Official support for "legacy" controllers
* Native support (including mDNS autodetection) for WiFi controllers
* Integrated specific gravity sensor support, including for Tilt Hydrometers and iSpindel devices

A full table of controllers/expected hardware availability is available [in the documentation](http://docs.fermentrack.com/en/master/hardware.html).


## Installation & Documentation

Full documentation for Fermentrack (including complete installation instructions) is available at [https://docs.fermentrack.com/](https://docs.fermentrack.com/).


### Quick Installation Instructions

1. Set up your Raspberry Pi (Install Raspbian, enable SSH)
2. Log into your Raspberry Pi via the terminal or SSH and run `curl -L install.fermentrack.com | sudo bash`
3. Wait for the installation to complete (can take ~45 mins) and log into Fermentrack 


## Requirements

Fermentrack is designed to be run as part of a Docker compose stack and should be able to run on most armv7/x86/x64-based systems that are capable of running docker-compose. Most users, however, will install Fermentrack on a Raspberry Pi.

**For Raspberry Pi-based Installs:**
* Raspberry Pi 2 B, 3, 4, 400, or later /w Internet Connection
* 2GB of free space available
* Fresh Raspberry Pi OS (Raspbian) install (Buster or later) preferred


**For x86/x64-based Installs:**
* Debian-based systems preferred (e.g. Ubuntu, Debian, etc)
* 2GB of free space available



## License
[![FOSSA Status](https://app.fossa.com/api/projects/git%2Bgithub.com%2Fthorrak%2Ffermentrack.svg?type=large)](https://app.fossa.com/projects/git%2Bgithub.com%2Fthorrak%2Ffermentrack?ref=badge_large)