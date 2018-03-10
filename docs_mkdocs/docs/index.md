# Fermentrack documentation

### What is Fermentrack?

Fermentrack is a web interface for controlling and monitoring fermentation temperature and progress. It interfaces with BrewPi controllers as well as specific gravity sensors like the Tilt and iSpindel in order to help you make better beer. Fermentrack is designed to be run on a Raspberry Pi, but can be used in most environments capable of running Python.

##### BrewPi Support

Fermentrack is a complete replacement for the web interface used by BrewPi written in Python using the Django web framework. In addition to the features bundled with brewpi-www, Fermentrack provides an easy install process, simple flashing of both Arduino-based and ESP8266-based BrewPi controllers, and the ability to control multiple chambers at once. Fermentrack also supports features such as WiFi and Bluetooth connectivity to help reduce clutter in your brewery. 

##### Specific Gravity Sensor Support

To help track your wort's progress on it's journey to become beer, Fermentrack supports multiple specific gravity 
sensors both on a standalone basis as well as in conjunction with BrewPi-based fermentation temperature controllers. 
Currently, Fermentrack supports [Tilt Hydrometers](https://tilthydrometer.com/) and 
[iSpindel devices](https://github.com/universam1/iSpindel) for automated gravity logging in addition to providing the 
ability to log manual gravity readings taken with traditional hydrometers or refractometers. 



### Included with Fermentrack

* **Fermentrack** - The Django-based replacement for brewpi-www. Licensed under MIT license.
* **brewpi-script** - Installed alongside Fermentrack is brewpi-script. Licensed under GPL v3.
* **BrewPi Firmware (Various)** - Fermentrack can be used to install various versions of the BrewPi firmware. Most of these are licensed under GPL v3, though other licenses may apply.
* **Other Firmware (Various)** - Fermentrack also can be used to install firmware such as iSpindel and BrewPiLess to compatible devices. Licenses may vary.

Other components used in or bundled with Fermentrack may have their own licensing requirements. These components can be referenced [here](about/components.md).

## New Features

One of the key reasons to write Fermentrack was to incorporate features that are missing in the official BrewPi web interface. The following are just some of the features that have been added:

* [Single Command Installation](install/index.md)
* Native multi-chamber support
* Cleaner, more intuitive controller setup
* Integrated support for ESP8266-based controllers
* Official support for "legacy" controllers
* Native support (including mDNS autodetection) for WiFi controllers
* Robust device detection for serial controllers 
* Support for Tilt and iSpindel specific gravity sensors


## Requirements

* Raspberry Pi Zero, Zero W, 2 B, or 3 /w Internet Connection
* Fresh Raspbian install 
* 1GB of free space available


## Getting Started with Fermentrack

[Getting started](install/index.md) with Fermentrack is incredibly easy! All you need to do is

1. [Install Raspbian](install/Raspi Setup.md) on your Raspberry Pi
1. [Install Fermentrack](install/index.md) (one command!)
1. [Configure Fermentrack](config/index.md#fully-automated)
1. Connect your [BrewPi temperature controllers](config/BrewPi Controller Setup.md) or specific gravity sensors
1. Configure your [BrewPi temperature controllers](config/BrewPi Controller Configuration.md) or specific gravity sensors

It can be done from start to finish in a bit under an hour, assuming all your hardware is assembled & ready to go.


## Other Notes

Fermentrack is currently designed for "legacy" brewpi firmware running on ESP8266 and Arduino hardware, and does not support "modern" firmware such as that included with official BrewPi controllers. 

A full table of controllers/expected hardware availability is available [in the documentation](hardware/index.md).


**PLEASE NOTE** - Fermentrack is currently intended to be installed on a fresh installation of Raspbian. It is **not** intended to be installed alongside brewpi-www and will conflict with the apache server brewpi-www installs.

