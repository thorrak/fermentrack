# Flashing a Controller

Fermentrack includes software which allows you to easily download & flash firmware to controllers. This feature is currently supported for the ESP8266 and Arduino architectures, and supports multiple families of firmware including BrewPi, BrewPiLess, and iSpindel. 

All devices will need be flashed via serial over USB - including devices you ultimately want to use over WiFi.

## Video Documentation

Prefer to watch a video of this process? [Click here to watch this on YouTube!](https://youtu.be/vpm-8k8tnGk) 

## Accessing the Flash Workflow

Flashing a new controller is accomplished through the controller flashing interface. This can be accessed directly or through the guided device setup workflow. From the device menu, choose "Flash Controller".


## Flashing a Controller

1. Once in the flash workflow, click "Refresh Firmware List from Fermentrack.com". This downloads a list of availble, screened firmware from Fermentrack.com.

1. After the list downloads, select your device family and click "Submit".

1. On the next screen, select the board (hardware variant) your device is based on. For some families, there may only be one option.

1. Double check your device family & board on the following screen and then ensure that the device you want to flash is **not** connected to the computer/device running Fermentrack. Once this is done click "Scan Devices"

1. Review the "Preexisting Devices" list to ensure that the device you want to flash is *not* listed. Assuming this is the case, connect the device you want to flash to the device running Fermentrack via a USB cable. Click "Scan for New Devices"

1. Your device should now be detected and displayed in the list. If it isn't, return to an earlier step and restart the process. Click the "Set Up" button next to your device.

1. On the following screen, select the firmware you want to flash to the device. Click "Flash to Device".

1. Once the firmware has flashed successfully, your device is ready to use! 

