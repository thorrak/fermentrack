brewpi-script
=============

This is a pared down version of the custom brewpi-script that was created for interfacing with ESP8266 BrewPi controllers. Brewpi-script logs the data, monitors the temperature profile and communicates with the BrewPi slave and the web server.

BrewPi-Script was originally created by Elco as part of the [BrewPi project](https://github.com/BrewPi/brewpi-script). 

This version has been modified by Thorrak & stone to add additional features and is maintained in a [separate repo](https://github.com/thorrak/brewpi-script).


Differences/New Features
-------

Differences from the official repo and new features include:

- Support for TCP serial connections (Including WiFi/Ethernet)
- Support for ESP8266-based controllers
- Support for web-based script configuration
- Support for multiple simultaneous instances of brewpi-script
- Removal of all arduino/firmware flashing routines


Licensing
-------
BrewPi-script is licensed under the **GPL v3**, a copy of which is included in LICENSE.md. 

This license may differ from that used for other associated projects, including the BrewPi firmware, BrewPi-www, Fermentrack, etc. 
