# Setting up a controller connected via Serial using Guided Workflow

Prior to setting up a controller with Fermentrack, please read the documentation specific to your controller's hardware. Supported hardware families include:
 
* [Arduino (and compatible)](../hardware/Arduino.md)
* [ESP8266](../hardware/ESP8266.md)
* [Spark Core](../hardware/Spark.md)
* [Native Python (Fuscus)](../hardware/Native%20Python.md)

When setting up a controller to connect via serial, the selected "port" is incredibly important, but is prone to change on reboot or as other devices are connected. Please read the "About Serial Port Autodetection" note below for information on how Fermentrack handles this issue. 

## Using the Guided Workflow

1. With the controller disconnected from the Raspberry Pi, launch guided setup and select "Add New Device (Guided)" from the "Select Device to Control" dropdown
2. Select the correct board type from the dropdown and click "Submit"
3. If your device is already flashed, choose "Yes - Already Flashed". If it isn't, read [these instructions](Flashing%20a%20Controller.md) before continuing. 
4. If setting up any device other than an ESP8266 click "Begin Serial Autodetection". If setting up an ESP8266, select "Serial" on the left, and then click "Begin Serial Autodetection"
5. Ensure that the controller is not connected to the Raspberry Pi, and click "Scan Devices"
6. Connect the controller to the Raspberry Pi
7. Click "Scan for New Devices"
8. Choose the device that corresponds to your Arduino and click "Set Up"
9. Enter a name for the device, adjust settings as needed, and click "Submit"


## About Serial Port Autodetection

By default, Linux assigns serial ports to devices like BrewPi controllers based on the order they are connected. If you have multiple devices connected to your Raspberry Pi this can mean that Fermentrack could potentially mistake one device for another. To prevent this, Fermentrack includes a feature which will disregard the specified serial port when connecting to the controller and will instead connect to the device with the USB serial number that matches the device you set up.

If you wish to disable this feature and instead only connect to the specified serial port, uncheck the "Prefer Connecting Via Udev" option in the "Manage Device" screen.

This feature only works on Linux-based operating systems (including Raspbian for Raspberry Pi), and may not work if Fermentrack is installed on a Mac or Windows-based computer.
