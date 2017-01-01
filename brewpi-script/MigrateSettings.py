# Copyright 2013 BrewPi
# This file is part of BrewPi.

# BrewPi is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# BrewPi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with BrewPi.  If not, see <http://www.gnu.org/licenses/>.

from collections import namedtuple, OrderedDict
from distutils.version import LooseVersion
import unittest

# SetttingMigrate containes 3 values:
# key: the JSON key for the version in maxVersion
# minVersion: the minimum version to restore from. Use 0 when all are valid.
# maxVersion: the maximum version to restore to. Use 1000 when the most current release is still valid
# alias: alternative keys from previous versions that should be interpreted as new key
#
SettingMigrate = namedtuple('SettingMigrate', ['key', 'minVersion', 'maxVersion', 'aliases'])

MigrateSettingsDefaultRestoreValidity = [
    SettingMigrate('tempFormat', '0', '1000', []),
    SettingMigrate('tempSetMin', '0', '0.2.11', []),
    SettingMigrate('tempSetMax', '0', '0.2.11', []),
    SettingMigrate('Kp', '0', '0.2.11', []),
    SettingMigrate('Ki', '0', '0.2.11', []),
    SettingMigrate('Kd', '0', '0.2.11', []),
    SettingMigrate('iMaxErr', '0', '0.2.11', []),
    SettingMigrate('pidMax', '0.2.4', '0.2.11', []),
    SettingMigrate('idleRangeH', '0', '0.2.11', []),
    SettingMigrate('idleRangeL', '0', '0.2.11', []),
    SettingMigrate('heatTargetH', '0', '0.2.11', []),
    SettingMigrate('heatTargetL', '0', '0.2.11', []),
    SettingMigrate('coolTargetH', '0', '0.2.11', []),
    SettingMigrate('coolTargetL', '0', '0.2.11', []),
    SettingMigrate('maxHeatTimeForEst', '0', '0.2.11', []),
    SettingMigrate('maxCoolTimeForEst', '0', '0.2.11', []),
    SettingMigrate('fridgeFastFilt', '0.2.0', '0.2.11', []),
    SettingMigrate('fridgeSlowFilt', '0.2.0', '0.2.11', []),
    SettingMigrate('fridgeSlopeFilt', '0.2.0', '0.2.11', []),
    SettingMigrate('beerFastFilt', '0.2.0', '0.2.11', []),
    SettingMigrate('beerSlowFilt', '0.2.3', '0.2.11', []),
    SettingMigrate('beerSlopeFilt', '0.2.3', '0.2.11', []),
    SettingMigrate('lah', '0', '0.2.11', []),
    SettingMigrate('hs', '0', '0.2.11', []),
    SettingMigrate('heatEst', '0', '0.2.11', []),
    SettingMigrate('coolEst', '0', '0.2.11', []),
    SettingMigrate('fridgeSet', '0', '1000', []),
    SettingMigrate('beerSet', '0', '1000', []),
    SettingMigrate('mode', '0', '1000', []),

    SettingMigrate('heater1_kp', '0.4.0', '1000', []),
    SettingMigrate('heater1_ti', '0.4.0', '1000', []),
    SettingMigrate('heater1_td', '0.4.0', '1000', []),
    SettingMigrate('heater1_infilt', '0.4.0', '1000', []),
    SettingMigrate('heater1_dfilt', '0.4.0', '1000', []),
    SettingMigrate('heater2_kp', '0.4.0', '1000', []),
    SettingMigrate('heater2_ti', '0.4.0', '1000', []),
    SettingMigrate('heater2_td', '0.4.0', '1000', []),
    SettingMigrate('heater2_infilt', '0.4.0', '1000', []),
    SettingMigrate('heater2_dfilt', '0.4.0', '1000', []),
    SettingMigrate('cooler_kp', '0.4.0', '1000', []),
    SettingMigrate('cooler_ti', '0.4.0', '1000', []),
    SettingMigrate('cooler_td', '0.4.0', '1000', []),
    SettingMigrate('cooler_infilt', '0.4.0', '1000', []),
    SettingMigrate('cooler_dfilt', '0.4.0', '1000', []),
    SettingMigrate('beer2fridge_kp', '0.4.0', '1000', []),
    SettingMigrate('beer2fridge_ti', '0.4.0', '1000', []),
    SettingMigrate('beer2fridge_td', '0.4.0', '1000', []),
    SettingMigrate('beer2fridge_infilt', '0.4.0', '1000', []),
    SettingMigrate('beer2fridge_dfilt', '0.4.0', '1000', []),
    SettingMigrate('beer2fridge_pidMax', '0.4.0', '1000', []),
    SettingMigrate('minCoolTime', '0.4.0', '1000', []),
    SettingMigrate('minCoolIdleTime', '0.4.0', '1000', []),
    SettingMigrate('heater1PwmPeriod', '0.4.0', '1000', []),
    SettingMigrate('heater2PwmPeriod', '0.4.0', '1000', []),
    SettingMigrate('coolerPwmPeriod', '0.4.0', '1000', []),
    SettingMigrate('deadTime', '0.4.0', '1000', [])
]

class MigrateSettings:

    def __init__(self, rv = None):
        '''
        :param rv: list of SettingMigrate namedtuples in the order they need to be restored
        '''
        if(rv == None):
            self.restoreValidity = MigrateSettingsDefaultRestoreValidity
        else:
            self.restoreValidity = rv

    def getKeyValuePairs(self, oldSettings, oldVersion, newVersion):
        '''
        Settings are in order to restore them and are read from the old settings
        Versions are compared to see which settings are still considered valid

        Keyword arguments:
        :param oldSettings: a dict of settings
        :param oldVersion: a string with the old version number
        :param newVersion: a string with the new version number
        :return keyValuePairs: OrderedDict of settings to restore
        :return oldSettings: settings that are not restored
        '''
        keyValuePairs = OrderedDict()
        oldSettingsCopy = oldSettings.copy() # get copy because we are removing items from the dict
        for setting in self.restoreValidity:
            for oldKey in [setting.key] + setting.aliases:
                if oldKey in oldSettingsCopy:
                    if (LooseVersion(oldVersion) >= LooseVersion(setting.minVersion) and
                            LooseVersion(newVersion) <= LooseVersion(setting.maxVersion)):
                        keyValuePairs[setting.key] = oldSettingsCopy.pop(oldKey)
                        break
        return keyValuePairs, oldSettingsCopy



class TestSettingsMigrate(unittest.TestCase):

    def testMinVersion(self):
        ''' Test if key is omitted when oldVersion < minVersion'''
        mg = MigrateSettings([
            SettingMigrate('key1', '0.2.0', '1000', []),
            SettingMigrate('key2', '0.1.1', '1000', []),
            ])
        oldSettings = {'key1': 1, 'key2': 2}
        restored, omitted = mg.getKeyValuePairs(oldSettings, '0.1.8', '0.3.0')
        self.assertEqual(restored,
                         OrderedDict([('key2', 2)]),
                         "Should only return key2")


    def testMaxVersion(self):
        ''' Test if key is omitted when newVersion > maxVersion'''
        mg = MigrateSettings([
            SettingMigrate('key1', '0.2.0', '0.3.0', []),
            SettingMigrate('key2', '0.1.1', '1000', []),
            ])
        oldSettings = {'key1': 1, 'key2': 2}
        restored, omitted = mg.getKeyValuePairs(oldSettings, '0.3.0', '0.4.0')
        self.assertEqual(restored,
                         OrderedDict([('key2', 2)]),
                         "Should only return key2")

    def testReturningNotRestored(self):
        mg = MigrateSettings([
            SettingMigrate('key1', '0.2.0', '0.3.0', []),
            SettingMigrate('key2', '0.1.1', '1000', []),
            ])
        oldSettings = {'key1': 1, 'key2': 2}
        restored, omitted = mg.getKeyValuePairs(oldSettings, '0.3.0', '0.4.0')
        self.assertEqual(restored,
                         OrderedDict([('key2', 2)]),
                         "Should only return key2")



    def testAliases(self):
        ''' Test if aliases for old keys result in the new key being returned with the old value'''
        mg = MigrateSettings([ SettingMigrate('key1', '0', '1000', ['key1a', 'key1b'])])
        oldSettings = {'key1a': 1}
        restored, omitted = mg.getKeyValuePairs(oldSettings, '1', '1')
        self.assertEqual(restored, OrderedDict([('key1', 1)]))


    def testBrewPiFilters(self):
        ''' Test if filters are only restored when old version > 0.2. The filter format was different earlier'''
        mg = MigrateSettings()
        oldSettings = {'fridgeFastFilt': 4}
        for oldVersion in ['0.1.0', '0.1.9', '0.1', '0.1.9.1']:
            restored, omitted = mg.getKeyValuePairs(oldSettings, oldVersion, '0.2.8')
            self.assertFalse('fridgeFastFilt' in restored,
                            "Filter settings should be omitted when older than version 0.2.0" +
                             ", failed on version " + oldVersion)
        for oldVersion in ['0.2.0', '0.2.4', '0.3', '1.0']:
            restored, omitted = mg.getKeyValuePairs(oldSettings, oldVersion, '2.0')
            self.assertTrue('fridgeFastFilt' in restored,
                            "Filter settings should be used when restoring from newer than version 0.2.0" +
                            ", failed on version " + oldVersion)


    def testPidMax(self):
        ''' Test if filters are only restored when old version > 0.2.4 It was not outputed correctly earlier'''
        mg = MigrateSettings()
        oldSettings = {'pidMax': 10.0}
        for oldVersion in ['0.1.0', '0.2', '0.2.3']:
            restored, omitted = mg.getKeyValuePairs(oldSettings, oldVersion, '0.2.8')
            self.assertFalse('pidMax' in restored,
                            "pidMax can only be trusted from version 0.2.4 or higher" +
                             ", failed on version " + oldVersion)
        for oldVersion in ['0.2.4', '0.2.5', '0.3', '1.0']:
            restored, omitted = mg.getKeyValuePairs(oldSettings, oldVersion, '2.0')
            self.assertTrue('pidMax' in restored,
                            "pidMax should be restored when restoring form version " + oldVersion)


    def testAllBrewPiSettings(self):
        ''' Test that when restoring from version 0.2.7 to 0.2.7 all settings are migrated'''
        from random import randint

        mg = MigrateSettings()
        oldSettings = dict()
        for setting in mg.restoreValidity:
            oldSettings[setting.key] = randint(0,100) # use random integer for old settings
        restored, omitted = mg.getKeyValuePairs(oldSettings, '0.2.7', '0.2.7')

        self.assertEqual(len(restored), len(oldSettings), "old and new settings should have same nr or items")

        count = 0
        for setting in restored:
            if count == 0:
                self.assertEqual(setting, 'tempFormat', "tempFormat should be restored as first setting")
            self.assertEqual(restored[setting], oldSettings[setting], "old value and restored value do not match")
            count += 1


if __name__ == "__main__":
    unittest.main()

