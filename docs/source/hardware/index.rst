.. include:: global.rst



Supported Hardware
====================

Fermentrack supports both BrewPi-based temperature controllers as well as various specific gravity sensors. Support for
each family of hardware varies, but is expanding with each release.


BrewPi Controllers
-------------------------

ESP8266-Based Controllers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Fermentrack was explicitly built to support :doc:esp8266, including flashing, setup, and ongoing logging/communication.
Controllers can be easily added/flashed through the Fermentrack web interface. Connection via either USB Serial or WiFi
is supported.


Arduino-Based Controllers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:doc:arduino can be easily installed/managed through the web interface, including flashing,
setup, and ongoing logging/communication.


Native Python (Fuscus)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Fermentrack currently supports :doc:`native python` controllers, but requires that software
installation/maintenance be done manually by the user. Fuscus devices can be controlled via Fermentrack's serial
connectivity support.

Spark Core/OEM Controllers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Unfortunately, Fermentrack does NOT support :doc:spark or other "modern" BrewPi controllers at this
time. Support is planed for a later date but is not currently prioritized.



Specific Gravity Sensors
--------------------------

Tilt Hydrometer
~~~~~~~~~~~~~~~~~~~

The `Tilt Hydrometer`_ is supported natively by Fermentrack which will assist with device setup. Tilt Hydrometers are
easy to use, and can be installed either alongside or independent of a temperature controller.

iSpindel
~~~~~~~~~~~

iSpindel_ devices are directly supported by Fermentrack which can assist with device configuration & calibration, as well
as the initial flashing of the iSpindel firmware.







Hardware Table of Contents
-------------------------------

.. toctree::
    :maxdepth: 1
    :caption: Installation Contents:

    arduino
    esp8266
    native python
    spark
