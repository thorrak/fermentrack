#!/usr/bin/env bash

# This script populates secretsettings.py (which contains the SECRET_KEY and not much else at the moment
# SECRET_KEY is a 50 character alphanumeric string that is used within Django
echo "Generating SECRET_KEY and writing to brewpi_django/secretsettings.py"

SECRET_KEY_STRING=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 50 | head -n 1)

rm "../brewpi_django/secretsettings.py"  # In case it exists
echo "SECRET_KEY = '${SECRET_KEY_STRING}'" >> "../brewpi_django/secretsettings.py"
echo "secretsettings.py created!\n"
