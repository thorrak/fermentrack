.. include:: ../global.rst

Adding a BrewPi Controller to Fermentrack
=============================================

Setting up a controller that is running the BrewPi firmware is easy, and Fermentrack will guide you every step of the
way. If you prefer to jump straight in and set the controller up manually, Fermentrack supports that too. Just jump ahead
to :ref:`manual_workflow`.

All of these instructions assume that you have already flashed the relevant firmware to your controller. If you just
built it and need to flash it, read :doc:`controller flashing` and complete that process before continuing.

.. warning:: Prior to setting up a controller with Fermentrack, please read any notes specific to your controller's hardware on the :doc:hardware page.


Setting up a WiFi-connected controller using the Guided Workflow
---------------------------------------------------------------------

#. After the controller is powered on and connected to your network, launch guided setup and select "Add New Device (Guided)" from the "Select Device to Control" dropdown
#. Select the correct board type (ESP8266) from the dropdown and click "Submit"
#. If your device is already flashed, choose "Yes - Already Flashed". If it isn't, read :doc:`controller flashing` before continuing.
#. Select "WiFi" on the left, and then click "Scan WiFi via mDNS"
#. Select the appropriate device from the "Available (Uninstalled) Devices" list, and click "Set Up"
#. Enter a name for the device, adjust settings as needed, and click "Submit"



Setting up a serial-connected controller using the Guided Workflow
----------------------------------------------------------------------

.. note:: When setting up a controller to connect via serial, the selected "port" is incredibly important, but is prone to change on reboot or as other devices are connected. Please read :ref:`serial_port_autodetection` for information on how Fermentrack handles this issue.

#. With the controller disconnected from the Raspberry Pi, launch guided setup and select "Add New Device (Guided)" from the "Select Device to Control" dropdown
#. Select the correct board type from the dropdown and click "Submit"
#. If your device is already flashed, choose "Yes - Already Flashed". If it isn't, read :doc:`controller flashing` before continuing.
#. If setting up any device other than an ESP8266 click "Begin Serial Autodetection". If setting up an ESP8266, select "Serial" on the left, and then click "Begin Serial Autodetection"
#. Ensure that the controller **is not** connected to the Raspberry Pi, and click "Scan Devices"
#. Connect the controller to the Raspberry Pi
#. Click "Scan for New Devices"
#. Choose the device that corresponds to your Arduino and click "Set Up"
#. Enter a name for the device, adjust settings as needed, and click "Submit"


.. _serial_port_autodetection:

About Serial Port Autodetection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By default, Linux assigns serial ports to devices like BrewPi controllers based on the order they are connected. If you
have multiple devices connected to your Raspberry Pi this can mean that Fermentrack could potentially mistake one device
for another. To prevent this, Fermentrack includes a feature which will disregard the specified serial port when
connecting to the controller and will instead connect to the device with the USB serial number that matches the device
you set up.

If you wish to disable this feature and instead only connect to the specified serial port, uncheck the "Prefer
Connecting Via Udev" option in the "Manage Device" screen.

This feature only works on Linux-based operating systems (including Raspbian for Raspberry Pi), and may not work if
Fermentrack is installed on a Mac or Windows-based computer.


.. _manual_workflow:

Setting up a controller using the Advanced (Manual) Workflow
--------------------------------------------------------------------


.. note:: When setting up a controller to connect via serial, the selected "port" is incredibly important, but is prone to change on reboot or as other devices are connected. Please read :ref:`serial_port_autodetection` for information on how Fermentrack handles this issue.

Setting up a controller using Advanced Workflow

1. Connect the controller to the Raspberry Pi
2. Launch guided setup and select "Add New Device (Advanced)"
3. Enter the configuration options associated with the device.

.. todo:: Rewrite the Manual Workflow section to document the available options, etc.

