# Copyright 2012 BrewPi/Elco Jacobs.
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

import time
import csv
import sys
import scriptlibs.BrewPiUtil as util


# also defined in brewpi.py. TODO: move to shared import
def logMessage(message):
    print >> sys.stderr, time.strftime("%b %d %Y %H:%M:%S   ") + message


def getNewTemp(scriptPath):
    temperatureReader = csv.reader(	open(util.addSlash(scriptPath) + 'settings/tempProfile.csv', 'rb'),
                                    delimiter=',', quoting=csv.QUOTE_ALL)
    temperatureReader.next()  # discard the first row, which is the table header
    prevTemp = None
    nextTemp = None
    interpolatedTemp = -99
    prevDate = None
    nextDate = None


    now = time.mktime(time.localtime())  # get current time in seconds since epoch

    for row in temperatureReader:
        dateString = row[0]
        try:
            date = time.mktime(time.strptime(dateString, "%Y-%m-%dT%H:%M:%S"))
        except ValueError:
            continue  # skip dates that cannot be parsed

        try:
            temperature = float(row[1])
        except ValueError:
            if row[1].strip() == '':
                # cell is left empty, this is allowed to disable temperature control in part of the profile
                temperature = None
            else:
                # invalid number string, skip this row
                continue

        prevTemp = nextTemp
        nextTemp = temperature
        prevDate = nextDate
        nextDate = date
        timeDiff = now - nextDate
        if timeDiff < 0:
            if prevDate is None:
                interpolatedTemp = nextTemp  # first set point is in the future
                break
            else:
                if prevTemp is None or nextTemp is None:
                    # When the previous or next temperature is an empty cell, disable temperature control.
                    # This is useful to stop temperature control after a while or to not start right away.
                    interpolatedTemp = None
                else:
                    interpolatedTemp = ((now - prevDate) / (nextDate - prevDate) * (nextTemp - prevTemp) + prevTemp)
                    interpolatedTemp = round(interpolatedTemp, 2)
                break

    if interpolatedTemp == -99:  # all set points in the past
        interpolatedTemp = nextTemp

    return interpolatedTemp
