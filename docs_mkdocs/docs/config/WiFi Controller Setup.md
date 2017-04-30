# Setting up a controller connected via WiFi using Guided Workflow

Prior to setting up a controller with Fermentrack, please read the documentation specific to your controller's hardware. Supported hardware families include:
 
* [Arduino (and compatible)](../hardware/Arduino.md)
* [ESP8266](../hardware/ESP8266.md)
* [Spark Core](../hardware/Spark.md)
* [Native Python (Fuscus)](../hardware/Native%20Python.md)


## Using the Guided Workflow

1. After the controller is powered on and connected to your network, launch guided setup and select "Add New Device (Guided)" from the "Select Device to Control" dropdown
2. Select the correct board type (ESP8266) from the dropdown and click "Submit"
3. If your device is already flashed, choose "Yes - Already Flashed". If it isn't, read [these instructions](Flashing%20a%20Controller.md) before continuing. 
4. Select "WiFi" on the left, and then click "Scan WiFi via mDNS"
5. Select the appropriate device from the "Available (Uninstalled) Devices" list, and click "Set Up"
6. Enter a name for the device, adjust settings as needed, and click "Submit"
