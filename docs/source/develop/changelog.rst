Changelog
====================

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/) because it was the first relatively standard format to pop up when I googled "changelog formats".


[Unreleased] - Bugfixes
~~~~~~~~~~~~~~~~~~~~~~~

Added
---------------------

- i386 (i686) build target for Docker images
- Custom color scheme support (dark mode!) (Thanks @calandryll!)


Changed
-------

- Change to prefer caching IPv4 addresses in BrewPiDevice.wifi_host_ip


Fixed
-----

- Properly allow blanks for BrewPiDevice.wifi_host_ip




[2021-04-05] - Docker Support
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Added
---------------------

- Added support for Docker installations
- Added environment/container version number to GitHub page
- Tilt "version" is now displayed on the Tilt Configuration page (Bluetooth only)
- Tilt battery level now shows on the Tilt Configuration page (Bluetooth v3/Tilt Pro only)
- "Last Check-in" time now added to Tilt configuration page (Bluetooth only)
- Added link to view Huey logs inside the Fermentrack UI
- Added link to view Circusd logs inside the Fermentrack UI


Changed
---------------------

- Removed instances where BrewPi-Script would write to the database
- Adjusted feedback loop for Circus to eliminate a potential race condition with transactional databases
- Redesigned available firmware list to reduce confusion
- Stale gravity check-in points will now not be displayed in the gravity dashboard panels
- Added support for latest TiltBridge firmware
- Remove unimplemented "TCP Socket" external push option
- Added Beer Setting, Fridge Setting, and Controller State to generic external push targets
- Upgraded TiltBridge support for v1.0.0 TiltBridges (earlier TiltBridge versions will now require manual configuration)
- External push target attempts now log to huey stdout
- Added battery to the GenericPushTarget message for pushed iSpindel devices


Fixed
---------------------

- Fermentrack now works with properly transactional databases (e.g. Postgres)
- Resolved issue causing false failures of the connectivity test (Thanks postalbunny!)
- Fixed issue preventing renaming of BrewPi controllers
- Dashes now allowed in TiltBridge mDNS IDs
- Corrected issue where iSpindel data couldn't be loaded if a data point wasn't availble in Redis



[2020-12-19] - Tilt Pro
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Added
---------------------

- iSpindel temperature readings can now be calibrated for accuracy
- Add properly sized app icon for apple devices


Changed
---------------------

- Added support for the new Tilt Pro
- Updated Sentry target
- Round iSpindel readings to four decimal places


Fixed
---------------------

- Updated requirements to support the new pip




[2020-11-07] - Temp Profile Tweaks & Docker Prep
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Added
---------------------

- Added optional "notes" field to fermentation profile models
- Added error message when attempting to create a point with an invalid temp/ttl in a temp profile
- Added support for configurable gravity units (e.g. plato, specific gravity)


Changed
---------------------

- Changed link to sqlite database to allow for a subdirectory in Docker installs
- Fermentation profile points can now be deleted for in-use fermentation profiles
- Remove Python 3.7 warning (everyone should have upgraded by now)
- If a Grainfather, Brewfather, or generic push target logging URL doesn't begin with http:// it is now automatically appended


Fixed
---------------------

- Bug causing errors when enabling beer profile mode
- Can now properly push to BrewFather when a fully populated temperature controller isn't linked
- Don't prompt new installs to run the script to fix old sqlite files



[2020-08-22] - Bugfixes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Added
---------------------

- Added pin definitions for esp32 BrewPi firmware
- Added Linux networking capability test to Tilt connectivity test suite


Changed
---------------------

- Added ability for BrewFather push target to push temps from BrewPi temp sensors


Fixed
---------------------

- Fixed bug that prevents reloading of cached controller objects
- Properly detect/force temperature conversion for iSpindel



[2020-06-05] - Django 3.0 Support
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Added
---------------------

- Added button to controller settings page to restart a controller


Changed
---------------------

- Updated code to be Django 3.0 Compatible
- Changed from Django 1.11 to Django 3.0
- Toggling display of a graph line on a temp controller's dashboard now clears the data point displayed in the legend
- Refactored brewpi-script to accept device IDs rather than names


Fixed
---------------------

- Properly catch exception when Redis test cannot connect to server
- Gravity and gravity temp colors when graphed on temp controller graphs will now display the correct color in the legend
- Links to CSVs from the beer log list now properly generate if the CSV exists
- Correct error detection/logging when a temp controller with an attached gravity sensor attempts to log before the gravity sensor logs its first point
- Properly check that a temperature setting is provided when setting a Beer or Fridge Constant mode for temp controllers
- Temp controller name uniqueness checks are now properly enforced in all add controller workflows



[2020-04-11] - Bugfixes & Tilt Troubleshooting
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Added
---------------------

- Added explicit support for LBussy's BrewPi-Remix I2C Board
- Exposed upgrade.log from the help screen
- Store the exact last time that a message was received from a Tilt to Redis
- Add sentry support to tilt_monitor_aio.py
- Added "debug" scripts for bluetooth Tilt connections
- Added TiltBridge connection settings to Tilt management page



Changed
---------------------

- Removed legacy Python 2 code
- Reduced gravity sensor temp precision to 0.1 degrees
- Locked pybluez, aioblescan, and redis versions to prevent undesired format changes going forward


Fixed
---------------------

- Fix display of TiltBridge mDNS settings on Tilt settings page

[2020-02-17] - Improved ESP32 Flashing Support
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Added
---------------------

- Added support for flashing a bootloader and otadata partition to ESP32 devices


Changed
---------------------

- SPIFFS partitions can now be flashed to ESP8266 devices


[2020-02-15] - ThingSpeak and Grainfather Support
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Added
---------------------

- Added support for pushing data to ThingSpeak (thanks @johndoyle!)
- Added support for pushing data to Grainfather (thanks @mp-se!)


Changed
---------------------

- Gravity sensors attached to BrewPi controllers will now send those controller's temps to Brewfather
- An explicit error message will now be displayed when a user attempts to manually access the ispindel endpoint


Fixed
---------------------

- Fixed where Fahrenheit readings coming from an iSpindel could be improperly reconverted to Fahrenheit
- Lock temperature display on dashboard panels to one decimal place
- Allow updates to controller settings when controller name isn't changing (for real this time)
- Fix bug that would default all Tilts to 'Bluetooth' even when a TiltBridge was selected
- Fixed issue where Tilt readings were not being properly decoded (Thanks NecroBrews!)
- Fixed issue where dashboard panels were not being updated (Thanks NecroBrews!)


[2019-12-15] - Brewer's Friend, Brewfather, and MacOS BLE Support
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Added
---------------------

- Added support for pushing gravity sensor data to Brewer's Friend
- Added support for pushing gravity sensor data to Brewfather
- Added BLE support for MacOS (thanks corbinstreehouse!)

Changed
---------------------

- Adding an external push target now triggers data to always be sent within 60 seconds regardless of push frequency

Fixed
---------------------

- Disable "View Full CSV" button if gravity/beer logs don't exist
- Properly cleanse booleans when changing site settings for Constance
- Allow updates to controller settings when controller name isn't changing
- Remove requirement for TiltBridge value in the TiltBridge model definition
- Ignore Tilt diagnostic codes that cause erroneous temperature/gravity readings



[2019-10-24] - Miscellaneous Bugfixes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Fixed
---------------------

- Prompt for reconfiguration if pin/address assignment fails on BrewPi Controller
- Validate device name uniqueness when adding a new BrewPi Controller
- Warn user when empty temperature is submitted alongside Fridge or Beer Constant mode
- Return debugging info when a connection to a WiFi BrewPi Controller is refused
- Properly handle errors in the first step of the firmware flash process
- When logging beer points on a gravity-enabled log, make sure the gravity sensor exists (or stop logging)
- Properly handle empty TiltBridge check-ins
- Before adding a Tilt that uses a TiltBridge, make sure the TiltBridge exists
- Return an error if a TiltBridge doesn't pass properly formed JSON
- Enforce uniqueness of a Beer name/logging device combination when the Beer is created
- Cause brewpi-script to terminate if the controller returns invalid control settings
- Return empty JSON for annotations if Beer doesn't exist


[2019-03-31] - TiltBridge Support
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Added
---------------------

- Added support for TiltBridge Tilt-to-WiFi devices

Changed
---------------------

- Removed Hex SHA display on GitHub update
- Tweaked backup count for log files to reduce clutter

Fixed
---------------------

- Fixed hostname lookup in connection debug when running on a nonstandard port
- Fixed multipart firmware flashing
- Remove Git branch switching prompt during initial setup
- Remove links to defunct Tilt logs
- Fixed OneWire address display on BrewPi "Assign Pin/Device" page
- Fix link to "load beer log" modal on device dashboard when no beer is loaded


[2019-03-17] - Firmware Flash Changes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Added
---------------------

- Added support for flashing multi-part firmware (eg partition tables)

Changed
---------------------

- Updated firmware_flash models to support additional device families
- Changed to version 2 of firmware_flash models


[2019-02-17] - External Push (Remote Logging) Support
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
