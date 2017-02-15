#!/usr/bin/env bash

unset CDPATH
myPath="$( cd "$( dirname "${BASH_SOURCE[0]}")" && pwd )"

# This script populates secretsettings.py (which contains the SECRET_KEY and not much else at the moment
# SECRET_KEY is a 50 character alphanumeric string that is used within Django
echo "Generating SECRET_KEY and writing to brewpi_django/secretsettings.py"

SECRET_KEY_STRING=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 50 | head -n 1)

if [ -f "$myPath/../brewpi_django/secretsettings.py" ]; then
  echo "Removing old secretsettings.py file.."
  rm "$myPath/../brewpi_django/secretsettings.py"  # In case it exists
fi

echo "SECRET_KEY = '${SECRET_KEY_STRING}'" >> "$myPath/../brewpi_django/secretsettings.py"
echo "secretsettings.py created!"
