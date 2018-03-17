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

from datetime import datetime
import time
import os
import re

jsonCols = ("\"cols\":[" +
            "{\"type\":\"datetime\",\"id\":\"Time\",\"label\":\"Time\"}," +
            "{\"type\":\"number\",\"id\":\"BeerTemp\",\"label\":\"Beer temperature\"}," +
            "{\"type\":\"number\",\"id\":\"BeerSet\",\"label\":\"Beer setting\"}," +
            "{\"type\":\"string\",\"id\":\"BeerAnn\",\"label\":\"Beer Annotate\"}," +
            "{\"type\":\"number\",\"id\":\"FridgeTemp\",\"label\":\"Fridge temperature\"}," +
            "{\"type\":\"number\",\"id\":\"FridgeSet\",\"label\":\"Fridge setting\"}," +
            "{\"type\":\"string\",\"id\":\"FridgeAnn\",\"label\":\"Fridge Annotate\"}," +
            "{\"type\":\"number\",\"id\":\"RoomTemp\",\"label\":\"Room temp.\"}," +
            "{\"type\":\"number\",\"id\":\"State\",\"label\":\"State\"}" +
            "]")


def fixJson(j):
	j = re.sub(r"'{\s*?(|\w)", r'{"\1', j)
	j = re.sub(r"',\s*?(|\w)", r',"\1', j)
	j = re.sub(r"'(|\w)?\s*:", r'\1":', j)
	j = re.sub(r"':\s*(|\w*)\s*(|[,}])", r':"\1"\2', j)
	return j


def addRow(jsonFileName, row):
	jsonFile = open(jsonFileName, "r+")
	jsonFile.seek(-3, 2)  # Go insert point to add the last row
	ch = jsonFile.read(1)
	jsonFile.seek(0, os.SEEK_CUR)
	# when alternating between reads and writes, the file contents should be flushed, see
	# http://bugs.python.org/issue3207. This prevents IOError, Errno 0
	if ch != '[':
		# not the first item
		jsonFile.write(',')
	newRow = {}
	newRow['Time'] = datetime.today()

	# insert something like this into the file:
	# {"c":[{"v":"Date(2012,8,26,0,1,0)"},{"v":18.96},{"v":19.0},null,{"v":19.94},{"v":19.6},null]},
	jsonFile.write(os.linesep)
	jsonFile.write("{\"c\":[")
	now = datetime.now()
	jsonFile.write("{{\"v\":\"Date({y},{M},{d},{h},{m},{s})\"}},".format(
		y=now.year, M=(now.month - 1), d=now.day, h=now.hour, m=now.minute, s=now.second))
	if row['BeerTemp'] is None:
		jsonFile.write("null,")
	else:
		jsonFile.write("{\"v\":" + str(row['BeerTemp']) + "},")

	if row['BeerSet'] is None:
		jsonFile.write("null,")
	else:
		jsonFile.write("{\"v\":" + str(row['BeerSet']) + "},")

	if row['BeerAnn'] is None:
		jsonFile.write("null,")
	else:
		jsonFile.write("{\"v\":\"" + str(row['BeerAnn']) + "\"},")

	if row['FridgeTemp'] is None:
		jsonFile.write("null,")
	else:
		jsonFile.write("{\"v\":" + str(row['FridgeTemp']) + "},")

	if row['FridgeSet'] is None:
		jsonFile.write("null,")
	else:
		jsonFile.write("{\"v\":" + str(row['FridgeSet']) + "},")

	if row['FridgeAnn'] is None:
		jsonFile.write("null,")
	else:
		jsonFile.write("{\"v\":\"" + str(row['FridgeAnn']) + "\"},")

	if row['RoomTemp'] is None:
		jsonFile.write("null,")
	else:
		jsonFile.write("{\"v\":" + str(row['RoomTemp']) + "},")

	if row['State'] is None:
		jsonFile.write("null")
	else:
		jsonFile.write("{\"v\":" + str(row['State']) + "}")

	# rewrite end of json file
	jsonFile.write("]}]}")
	jsonFile.close()


def newEmptyFile(jsonFileName):
	jsonFile = open(jsonFileName, "w")
	jsonFile.write("{" + jsonCols + ",\"rows\":[]}")
	jsonFile.close()
