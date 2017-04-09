# Fermentrack and Arduino-based Controllers

Fermentrack currently supports Arduino-based controllers connected via Serial (USB) via either the "advanced" or "guided" setup workflow.

Fermentrack does **not** currently support flashing firmware to devices - to use an Arduino-based controller you will need to flash it before setting up with Fermentrack.


## Setting up a controller using Guided Workflow

1. With the controller disconnected from the Raspberry Pi, launch guided setup and select "Add New Device (Guided)" from the "Select Device to Control" dropdown
2. Select "Arduino (and compatible)" from the dropdown and click "Submit"
3. Choose "Yes - Already Flashed" and click "Begin Serial Autodetection". **NOTE** - If your device is NOT already flashed, stop here and flash it. Fermentrack cannot currently flash firmware to controllers.
4. Ensure that the controller is not connected to the Raspberry Pi, and click "Scan Devices"
5. Connect the controller to the Raspberry Pi
6. Click "Scan for New Devices"
7. Choose the device that corresponds to your Arduino and click "Set Up"
8. Enter a name for the device, adjust settings as needed, and click "Submit"


## Setting up a controller using Advanced Workflow

1. Connect the controller to the Raspberry Pi
2. Launch guided setup and select "Add New Device (Advanced)"
3. Enter the configuration options associated with the device. Be sure to select "serial" as the connection type, and specify the correct serial port for the controller. Do not select "auto" as the serial port as this is unlikely to work.


