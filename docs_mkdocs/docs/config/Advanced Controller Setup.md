# Setting up a controller using the Advanced (Manual) Workflow

Prior to setting up a controller with Fermentrack, please read the documentation specific to your controller's hardware. Supported hardware families include:
 
* [Arduino (and compatible)](../hardware/Arduino.md)
* [ESP8266](../hardware/ESP8266.md)
* [Spark Core](../hardware/Spark.md)
* [Native Python (Fuscus)](../hardware/Native%20Python.md)

Controllers can be se up to connect via both WiFi and serial. When setting up a controller to connect via serial the selected "port" is incredibly important but is prone to change on reboot or as other devices are connected. Please read the "About Serial Port Autodetection" note below for information on how Fermentrack handles this issue. 

## Setting up a controller using Advanced Workflow

1. Connect the controller to the Raspberry Pi
2. Launch guided setup and select "Add New Device (Advanced)"
3. Enter the configuration options associated with the device.


## About Serial Port Autodetection

By default, Linux assigns serial ports to devices like BrewPi controllers based on the order they are connected. If you have multiple devices connected to your Raspberry Pi this can mean that Fermentrack could potentially mistake one device for another. To prevent this, Fermentrack includes a feature which will disregard the specified serial port when connecting to the controller and will instead connect to the device with the USB serial number that matches the device you set up.

If you wish to disable this feature and instead only connect to the specified serial port, uncheck the "Prefer Connecting Via Udev" option in the "Manage Device" screen.

This feature only works on Linux-based operating systems (including Raspbian for Raspberry Pi), and may not work if Fermentrack is installed on a Mac or Windows-based computer.
