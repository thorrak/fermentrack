Changelog
====================

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/) because it was the first relatively standard format to pop up when I googled "changelog formats".


[2019-03-17] - Firmware Flash Changes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Added
---------------------

- Added support for flashing multi-part firmware (eg partition tables)

Changed
---------------------

- Updated firmware_flash models to support additional device families
- Changed to version 2 of firmware_flash models


[2019-02-17] - External Push (Remote Logging) Support
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Added
---------------------

- Fermentrack can now periodically "push" readings out to an external device/app
- Added "new control constants" support for "modern" controllers

Fixed
---------------------

- Explicitly linked Favicon from template
- Fixed BrewPi-Script error when attempting to use feature not available in Python 3.4
- Properly catch error in BrewPi-Script when pidfile already exists
- Added filesize check for gravity sensor & brewpi-device logfiles
- Add support for temperature calibration offsets


[2019-02-17] - External Push (Remote Logging) Support
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Added
---------------------

- Fermentrack can now periodically "push" readings out to an external device/app
- Added "new control constants" support for "modern" controllers

Fixed
---------------------

- Explicitly linked Favicon from template
- Fixed BrewPi-Script error when attempting to use feature not available in Python 3.4
- Properly catch error in BrewPi-Script when pidfile already exists
- Added filesize check for gravity sensor & brewpi-device logfiles
- Add support for temperature calibration offsets


[2018-10-24] - Tilt Monitor Refactoring
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Changed
---------------------

- The Tilt Hydrometer monitor now uses aioblescan instead of beacontools for better reliability
- Added support for smaller screen sizes

Fixed
---------------------

- Tilt Hydrometers will now properly record temperatures measured in Celsius


[2018-08-05] - Gravity Refactoring
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Added
---------------------

- DS18b20 sensors can now have temperature offsets added to each reading to correct for calibration errors
- ESP8266 controllers can now have their WiFi settings reset via the "manage sensor" web interface
- Control constants form now supports both "new" (OEM BrewPi) and "old" ("Legacy" branch) control constants
- Tilt hydrometers can now have their specific gravity readings calibrated
- "Heat/Cool State" will now be shown on temperature graphs
- Fermentrack logo added as favicon


Changed
---------------------

- The iSpindel endpoint can now be accessed at either /ispindel or /ispindle
- Specific gravity will now be shown on graphs with 3 decimal places
- Beer log format has been changed to add state information

Fixed
---------------------

- Removed constant LCD polling for "modern" controllers
- Gravity support will now be properly disabled when the correct flag is set at setup
- iSpindel devices that do not report all 'extras' will no longer throw errors when reporting gravity



[2018-04-27] - "v1.0 release"
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Added
---------------------

- Added fermentation controller "Manage Device" page
- Upgrades are now logged to upgrade.log
- Controller "stdout" and "stderr" logs are now saved/accessible
- Support for serial devices
- Support for Arduino-based devices
- Support for in-app git branch switching
- Autodetection of serial devices
- Huey (delayed/scheduled task) support (currently unused)
- Controllers connected via serial can now have their serial port autodetected using the udev serial number
- Beer profiles are now displayed in graph form
- Firmware can now be flashed to new Arduino & ESP8266-based controllers from within the app
- Preferred timezone can now be selected for use throughout Fermentrack
- Beer log management (deletion/downloading)
- Added configuration options for graph line colors
- Graph lines can be toggled by clicking the icon in the legend
- Added support for specific gravity sensors
- Added support for Tilt Hydrometers
- Added support for iSpindel specific gravity sensors


Changed
---------------------

- Inversion flag for installed devices is now shown on the "configure pins/sensors" page
- Form errors are now displayed on "configure pins/sensors" page
- Beer logs are no longer deleted along with the parent device (but they will become inaccessible from within Fermentrack)
- GitHub updates are no longer triggered automatically by visiting the update page, and must now be manually triggered by clicking a button
- The IP address of a BrewPiDevice is now cached, and can be used if mDNS stops working
- At end of a fermentation profile the controller will now be switched to beer constant mode
- All data points are now explicitly recorded in UTC
- Added icon to graph legend to display line color
- Updated to Django v1.11 (Long term support version)
- Changed from supporting Python 2 to Python 3


Fixed
---------------------

- Inversion state no longer improperly defaults
- Minimum graph size adjusted to account for smaller displays
- Changed on_delete behavior to allow deletion of fermentation controllers
- Git update check will now properly wait between checks if up to date
- GIT_UPDATE_TYPE of 'none' will now properly disable update checks
- BrewPi controllers now accept unicode names
- "View Room Temp" link on Dashboard now functions
- Room temp now included in legend for graphs



[2017-03-17] - "v0.1 release"
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Added
---------------------

- First release!
