# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/) because it was the first relatively standard format to pop up when I googled "changelog formats".


## [Unversioned]
### Added
- Added fermentation controller "Manage Device" page
- Upgrades are now logged to upgrade.log
- Controller "stdout" and "stderr" logs are now saved/accessible
- Support for serial devices
- Support for Arduino-based devices
- Support for in-app git branch switching
- Autodetection of serial devices
- Celery (delayed/scheduled task) support (currently unused)

### Changed
- Inversion flag for installed devices is now shown on the "configure pins/sensors" page
- Form errors are now displayed on "configure pins/sensors" page
- Beer logs are no longer deleted along with the parent device (but they will become inaccessible from within Fermentrack)
- GitHub updates are no longer triggered automatically by visititing the update page, and must now be manually triggered by clicking a button
- The IP address of a BrewPiDevice is now cached, and can be used if mDNS stops working

### Fixed
- Inversion state no longer improperly defaults
- Minimum graph size adjusted to account for smaller displays
- Changed on_delete behavior to allow deletion of fermentation controllers
- Git update check will now properly wait between checks if up to date
- GIT_UPDATE_TYPE of 'none' will now properly disable update checks
- BrewPi controllers now accept unicode names

## [0.1.0] - 2017-03-17 - "v1 release"
### Added
- First release!
