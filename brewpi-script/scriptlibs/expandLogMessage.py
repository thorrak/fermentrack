# Copyright 2012 BrewPi
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

from __future__ import print_function, absolute_import

import json
from . import parseEnum
import os
import re

logMessagesFile = os.path.dirname(__file__) + '/LogMessages.h'

errorDict = parseEnum.parseEnumInFile(logMessagesFile, 'errorMessages')
infoDict = parseEnum.parseEnumInFile(logMessagesFile, 'infoMessages')
warningDict = parseEnum.parseEnumInFile(logMessagesFile, 'warningMessages')


def valToFunction(val):
    functions = ['None',  # 0
                 'Chamber Door',  # 1
                 'Chamber Heater',  # 2
                 'Chamber Cooler',  # 3
                 'Chamber Light',  # 4
                 'Chamber Temp',  # 5
                 'Room Temp',  # 6
                 'Chamber Fan',  # 7
                 'Chamber Reserved 1',  # 8
                 'Beer Temp',  # 9
                 'Beer Temperature 2',  # 10
                 'Beer Heater',  # 11
                 'Beer Cooler',  # 12
                 'Beer S.G.',  # 13
                 'Beer Reserved 1',  # 14
                 'Beer Reserved 2']  # 15
    if val < len(functions):
        return functions[val]
    else:
        return 'Unknown Device Function'


def getVersion():
    hFile = open(logMessagesFile)
    for line in hFile:
        if 'BREWPI_LOG_MESSAGES_VERSION ' in line:
            splitLine = line.split('BREWPI_LOG_MESSAGES_VERSION')
            return int(splitLine[1])  # return version number
    print("ERROR: could not find version number in log messages header file", flush=True)
    return 0


def expandLogMessage(logMessageJsonString):
    expanded = ""
    logMessageJson = json.loads(logMessageJsonString)
    logId = int(logMessageJson['logID'])
    logType = logMessageJson['logType']
    values = logMessageJson['V']
    dict = 0
    logTypeString = "**UNKNOWN MESSAGE TYPE**"
    if logType == "E":
        dict = errorDict
        logTypeString = "ERROR"
    elif logType == "W":
        dict = warningDict
        logTypeString = "WARNING"
    elif logType == "I":
        dict = infoDict
        logTypeString = "INFO MESSAGE"

    if logId in dict:
        expanded += logTypeString + " "
        expanded += str(logId) + ": "
        count = 0
        for v in values:
            try:
                if dict[logId]['paramNames'][count] == "config.deviceFunction":
                    values[count] = valToFunction(v)
                elif dict[logId]['paramNames'][count] == "character":
                    if values[count] == -1:
                        # No character received
                        values[count] = 'END OF INPUT'
                    else:
                        values[count] = chr(values[count])
            except IndexError:
                pass
            count += 1
        printString = dict[logId]['logString'].replace("%d", "%s").replace("%c", "%s")
        numVars = printString.count("%s")
        numReceived = len(values)
        if numVars == numReceived:
            expanded += printString % tuple(values)
        else:
            expanded += printString + "  | Number of arguments mismatch!, expected " + str(
                numVars) + "arguments, received " + str(values)
    else:
        expanded += logTypeString + " with unknown ID " + str(logId)

    return expanded


def filterOutLogMessages(input_string):
    # removes log messages from string received from Serial
    # log messages are sometimes printed in the middle of a JSON string, which causes decode errors
    # this function filters them out and prints them
    m = re.compile("D:\{.*?\}\r?\n")
    log_messages = m.findall(input_string)
    stripped = m.sub('', input_string)

    return (stripped, log_messages)


if __name__ == '__main__':
    # Quick dirty test (this code will be removed when ControlBox is ready anyway
    test_string = 'd:[{"i":0,"t":4,"c":1,"b":0,"f":2,"h":1,"d":0,"p":17,"v":0.0,"x":0}D:{"logType":"I","logID":22,"V":["3AB0122100000098"]}\r\n,{"i":2,"t":5,"c":1,"b":0,"f":8,"h":3,"d":0,"p":0,"v":0,"x":0,"a":"3AB0122100000098","n":1}]'
    stripped, messages = filterOutLogMessages(test_string)
    print('Stripped line: {0}'.format(stripped))
    print('messages: {0}'.format(messages))

getVersion()
