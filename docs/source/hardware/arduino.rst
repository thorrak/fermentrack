.. include:: global.rst


Arduino & Compatible Controllers
==================================

Fermentrack currently has native support for Arduino-based controllers connected via Serial (USB).

By default, Fermentrack will detect the USB serial number associated with your Arduino when initially configured, and
will use that - instead of the specified serial port - to connect. For more information, read the "About Serial Port
Autodetection" note in the ["Guided Setup" instructions](../config/BrewPi Controller Setup.md#setting-up-a-serial-connected-controller).

.. todo:: Update the link above


Setting Up an Arduino-based Controller in Fermentrack
--------------------------------------------------------

There are two options for setting up a controller in Fermentrack - Guided Setup and Advanced (Manual) Setup.

[**Guided Setup**](../config/BrewPi Controller Setup.md#setting-up-a-serial-connected-controller) - Instructions are available [here](../config/BrewPi Controller Setup.md#setting-up-a-serial-connected-controller). When choosing the board type, select "Arduino (and compatible)" from the dropdown.

[**Manual Setup**](../config/Advanced Controller Setup.md) - Instructions are available [here](../config/Advanced Controller Setup.md).


Bluetooth Support
-------------------

There is a third party project which looks to add bluetooth support for Arduino (and similar) controllers to BrewPi.
While this project is not natively supported from within Fermentrack, at the end the project presents the BrewPi
controller as a device connected via serial which allows it to be set up within Fermentrack via the Manual Setup
workflow.

