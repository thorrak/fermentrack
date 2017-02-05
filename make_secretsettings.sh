#!/usr/bin/env bash

# This script populates secretsettings.py (which contains the SECRET_KEY and not much else at the moment
# SECRET_KEY is a 50 character alphanumeric string that is used within Django
SECRET_KEY_STRING=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 50 | head -n 1)

echo "SECRET_KEY = '${SECRET_KEY_STRING}'" >> "brewpi_django/secretsettings.py"
