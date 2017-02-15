#Fermentrack documentation

###What is Fermentrack?

Fermentrack is a complete replacement for the web interface used by BrewPi written in Python using the Django web framework. It is designed to be used alongside a rewritten BrewPi-Script as well as ESP8266-based BrewPi controllers. Support for other BrewPi controllers (Arduino, Spark, and Fuscus) will be forthcoming. 

Fermentrack is currently intended to be installed on a fresh installation of Raspbian and will conflict with brewpi-www if installed on the same server. 


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

## Missing Features

At the moment, Fermentrack doesn't support 100% of the features of the official BrewPi web client. Some of these missing features (as well as the version they are expected to be added) include:

* Serial controller support (expected in v2)
* Serial controller autodetection (v2)
* Arduino support (v2)
* Spark/Fuscus support (v3)
* Fuscus support (v3)
* Support for "modern" (non-legacy branch) controllers (v3)


## Requirements

* Raspberry Pi Zero, 2 B, or 3 /w Internet Connection
* Fresh Raspbian install (Lite or /w Pixel supported, Oct 2016 version or later)
* 

**PLEASE NOTE** - Fermentrack is currently intended to be installed on a fresh installation of Raspbian. It is **not** intended to be installed alongside brewpi-www and will conflict 






Look - I haven't written any documentation for this yet, but I figure everything has to start somewhere.

This is a pretty standard Django app for most intents and purposes. You'll need to create the database (manage.py migrate iirc) - I'm targeting SQLite due to the easy deployment, but nothing prevents using postgres or mysql if that's what you prefer. You'll also need to create a superuser (manage.py createsuperuser) if you want to use the admin. It's optional.

The last thing you'll need to do is create the /fermentrack_django/secretsettings.py file. I've created an example of this file called /fermentrack_django/secretsettings.py.example . It's basic, for now.

If you think about the main BrewPi project, you have three main components - BrewPi-www, BrewPi-script, and the BrewPi firmware. This project seeks to replace BrewPi-www, and uses a replacement for BrewPi-script (which is in a subdirectory of the same name). Using this instance of Brewpi-script is mandatory for this project to function.
