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

import re

def parseEnumInFile(hFilePath, enumName):
	messageDict = {}
	hFile = open(hFilePath)
	regex = re.compile("[A-Z]+\(([A-Za-z][A-Z0-9a-z_]*),\s*\"([^\"]*)\"((?:\s*,\s*[A-Za-z][A-Z0-9a-z_\.]*\s*)*)\)\s*,?")
	for line in hFile:
		if 'enum ' + enumName in line:
			break  # skip lines until enum open is encountered

	count = 0
	for line in hFile:
		if 'MSG(' in line:
			# print line
			# print regex
			# r = regex.search(str(line))
			groups = regex.findall(line)
			logKey = groups[0][0]
			logString = groups[0][1]
			paramNames = groups[0][2].replace(",", " ").split()
			messageDict[count] = {'logKey': logKey, 'logString': logString,'paramNames': paramNames}
			count += 1

		if 'END enum ' + enumName in line:
			break

	hFile.close()
	return messageDict

