#!/usr/bin/env python
import os
import sys
from django.db import IntegrityError
# from app.management.commands.fix_sqlite_for_django_2 import Command as fix_sqlite_command

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fermentrack_django.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError:
        # The above import may fail for some other reason. Ensure that the
        # issue is really that Django is missing to avoid masking other
        # exceptions on Python 2.
        try:
            import django
        except ImportError:
            raise ImportError(
                "Couldn't import Django. Are you sure it's installed and "
                "available on your PYTHONPATH environment variable? Did you "
                "forget to activate a virtual environment?"
            )
        raise
    try:
        execute_from_command_line(sys.argv)
    except IntegrityError:
        # If we have an integrity error, it's most likely because of the Django 2 SQLite issue. Trigger the fix, then
        # reattempt the initial migration.
        execute_from_command_line(['manage.py', 'fix_sqlite_for_django_2'])
        execute_from_command_line(sys.argv)

