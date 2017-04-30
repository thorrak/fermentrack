# Fermentrack and Arduino-based Controllers

Fermentrack currently supports Arduino-based controllers connected via Serial (USB).

Fermentrack does **not** currently support flashing firmware to devices - to use an Arduino-based controller you will need to flash it before setting up with Fermentrack.

By default, Fermentrack will detect the USB serial number associated with your Arduino when initially configured, and will use that - instead of the specified serial port - to connect. For more information, read the "About Serial Port Autodetection" note in the ["Guided Setup" instructions](../config/Serial%20Controller%20Setup.md).


## Setting Up an Arduino-based Controller in Fermentrack

There are two options for setting up a controller in Fermentrack - Guided Setup and Advanced (Manual) Setup.

[**Guided Setup**](../config/Serial%20Controller%20Setup.md) - Instructions are available [here](../config/Serial%20Controller%20Setup.md). When choosing the board type, select "Arduino (and compatible)" from the dropdown.

[**Manual Setup**](../config/Advanced%20Controller%20Setup.md) - Instructions are available [here](../config/Advanced%20Controller%20Setup.md).
