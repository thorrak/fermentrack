.. include:: global.rst



Supported Hardware
====================

Fermentrack supports both BrewPi-based temperature controllers as well as various specific gravity sensors. Support for
each family of hardware varies, but is expanding with each release.


BrewPi Controllers
-------------------------

ESP8266-Based Controllers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Fermentrack was explicitly built to support ESP8266-based controllers regardless of connection method (WiFi or Serial).

For more information on ESP8266-based firmware, please refer to one of the following:

* `BrewPi-ESP8266 GitHub`_
* `BrewPi-ESP8266 HomeBrewTalk Thread`_

If connecting an ESP8266-based controller via serial, please note that by default Fermentrack will detect the USB serial
number associated with your ESP8266 when initially configured, and will use that *instead of the specified serial port*
to connect. For more information, read :ref:`serial_port_autodetection`.



Arduino-Based Controllers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Fermentrack currently has native support for Arduino-based controllers connected via Serial (USB).

By default, Fermentrack will detect the USB serial number associated with your Arduino when initially configured, and
will use that - instead of the specified serial port - to connect. For more information, read
:ref:`serial_port_autodetection`.



Bluetooth Support for BrewPi-Controllers
****************************************

There is a third party project which looks to add bluetooth support for Arduino (and similar) controllers to BrewPi.
While this project is not natively supported from within Fermentrack, at the end the project presents the BrewPi
controller as a device connected via serial which allows it to be set up within Fermentrack via the Manual Setup
workflow.




Native Python (Fuscus)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Fuscus_ is a project which implements the legacy (Arduino) BrewPi featureset directly on the Raspberry Pi with no need
for an external controller.

As of now, serial connections are supported by Fermentrack, and therefore it is expected that Fuscus should be
Fermentrack compatible. Fuscus support *has not been tested* and should be considered experimental.

Due to the nature of the serial ports used by Fuscus, the serial autodetection process cannot be used to set up a
Fuscus-based controller. To set up, please follow the instructions in :ref:`manual_workflow`.

.. note:: When setting up a Fuscus-based controller in the manual workflow, make sure to set "prefer_connecting_via_udev"
 to False. If it is set to true, BrewPi-Script may either not connect or connect to the wrong device.


Further down the development path are other features involving Fuscus such as direct installation and configuration
management - though these are expected in v3 and beyond.



Spark Core/OEM Controllers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Currently, Fermentrack does not support Spark-based controllers. Support for Spark based controllers is planned, but
will be implemented at a much later date. Once implemented, Fermentrack will support controlling both legacy
(Arduino/Fuscus) and modern (Spark) controllers from the same installation.








Specific Gravity Sensors
--------------------------

Tilt Hydrometer
~~~~~~~~~~~~~~~~~~~

The `Tilt Hydrometer`_ is supported natively by Fermentrack which will assist with device setup. Tilt Hydrometers are
easy to use, and can be installed either alongside or independent of a temperature controller. Natively, Tilt
Hydrometers communicate via Bluetooth, however they can also be connected via the TiltBridge_ Bluetooth-to-WiFi adaptor.


iSpindel
~~~~~~~~~~~

iSpindel_ devices are directly supported by Fermentrack which can assist with device configuration & calibration, as well
as the initial flashing of the iSpindel firmware.


