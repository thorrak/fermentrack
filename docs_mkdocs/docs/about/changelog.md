# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/) because it was the first relatively standard format to pop up when I googled "changelog formats".


## [Unversioned]
### Added
- Added fermentation controller "Manage Device" page
- Fermentation controllers 
- Upgrades are now logged to upgrade.log
- Controller "stdout" and "stderr" logs are now saved/accessible
### Changed
- Inversion flag for installed devices is now shown on the "configure pins/sensors" page
- Form errors are now displayed on "configure pins/sensors" page
- Beer logs are no longer deleted along with the parent device (but they will become inaccessible from within Fermentrack)
### Fixed
- Inversion state no longer improperly defaults
- Minimum graph size adjusted to account for smaller displays
- Changed on_delete behavior to allow deletion of fermentation controllers


## [0.1.0] - 2017-03-17 - "v1 release"
### Added
- First release!
