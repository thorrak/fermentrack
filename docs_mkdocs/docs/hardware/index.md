# Supported Hardware

Fermentrack supports both BrewPi-based temperature controllers as well as various specific gravity sensors. Support for
each family of hardware varies, but is expanding with each release.


### BrewPi Controllers

##### ESP8266-Based Controllers

Fermentrack was explicitly built to support [ESP8266-based controllers](ESP8266.md), including flashing, setup, and
ongoing logging/communication. Controllers can be easily added/flashed through the Fermentrack web interface. 
Additional information can be found [here](ESP8266.md).

##### Arduino-Based Controllers

[Arduino-based controllers](Arduino.md) can be easily installed/managed through the web interface, including flashing,
setup, and ongoing logging/communication. Additional information can be found [here](Arduino.md)

##### Native Python (Fuscus)

Fermentrack currently supports [native python (Fuscus)](Native Python.md) controllers, but requires that software 
installation/maintenance be done manually by the user. Fuscus devices can be controlled via Fermentrack's serial
connectivity support.

##### Spark Core/OEM Controllers

Unfortunately, Fermentrack does NOT support [Spark-based](Spark.md), OEM, or other "modern" BrewPi controllers at this 
time. Support is planed for a later date, but is not currently prioritized.



### Specific Gravity Sensors

##### Tilt Hydrometer

Tilt Hydrometers are supported natively by Fermentrack which will assist with device setup. Tilt hydrometers are easy to
use, and can be installed either alongside or independent of a temperature controller.

##### iSpindel

iSpindel devices are directly supported by Fermentrack which can assist with device configuration & calibration, as well
as the initial flashing of the iSpindel firmware. 

