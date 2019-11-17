#!/usr/bin/env bash

unset CDPATH
myPath="$( cd "$( dirname "${BASH_SOURCE[0]}")" && pwd )"

# This script populates secretsettings.py (which contains the SECRET_KEY and not much else at the moment
# SECRET_KEY is a 50 character alphanumeric string that is used within Django
echo "Generating SECRET_KEY and writing to fermentrack_django/secretsettings.py"

 #LC_CTYPE=C is needed for tr on macos, otherwise we get illegal byte errors
SECRET_KEY_STRING=$(LC_CTYPE=C tr -dc 'a-zA-Z0-9' < /dev/urandom | fold -w 50 | head -n 1)

if [ -f "$myPath/../fermentrack_django/secretsettings.py" ]; then
  echo "Removing old secretsettings.py file.."
  rm "$myPath/../fermentrack_django/secretsettings.py"  # In case it exists
fi

echo "SECRET_KEY = '${SECRET_KEY_STRING}'" >> "$myPath/../fermentrack_django/secretsettings.py"
echo "secretsettings.py created!"
