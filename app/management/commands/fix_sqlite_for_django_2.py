from __future__ import with_statement

from django.core.management.base import BaseCommand  # , CommandError

from django.apps import apps
from django.db import connection
from constance import config
import shutil

import django.db.utils

import firmware_flash.models

# For monkey patching (see below)
from django.db.backends.sqlite3.schema import DatabaseSchemaEditor, BaseDatabaseSchemaEditor

from django.core.management import execute_from_command_line


class Command(BaseCommand):
    help = "Fixes SQLite databases that have been migrated from Django 1.x to Django 2.0+"

    def clear_firmware_data(self):
        print("Clearing firmware_flash.Firmware objects...")
        constraint_check = connection.disable_constraint_checking()
        firmware_flash.models.Firmware.objects.all().delete()

        print("Clearing firmware_flash.Board objects...")
        constraint_check = connection.disable_constraint_checking()
        firmware_flash.models.Board.objects.all().delete()

        print("Clearing firmware_flash.DeviceFamily objects...")
        constraint_check = connection.disable_constraint_checking()
        firmware_flash.models.DeviceFamily.objects.all().delete()

        print("Clearing firmware_flash.Project objects...")
        constraint_check = connection.disable_constraint_checking()
        firmware_flash.models.Project.objects.all().delete()


        print("Done clearing firmware_flash objects...")


    def fix_sqlite_for_django_2(self):
        # We're monkey patching the __exit__ method of DatabaseSchemaEditor because it reenables constraint checking
        # which we explicitly DO NOT want to do. The problem is that without patching this if multiple tables have
        # incorrect foreign key constraints you can't fix one at a time - you have to fix both simultaneously (which
        # Django doesn't support). Fun times.
        DatabaseSchemaEditor.__exit__ = BaseDatabaseSchemaEditor.__exit__

        try:
            constraint_check = connection.disable_constraint_checking()
        except:
            connection.connection = connection.connect()
            constraint_check = connection.disable_constraint_checking()


        # Back up the sqlite databases before we start rebuilding things, just in case.
        # ol2 -> ol3
        try:
            shutil.copyfile("db.sqlite3.ol2", "db.sqlite3.ol3")
        except FileNotFoundError:
            pass
        # old -> ol2
        try:
            shutil.copyfile("db.sqlite3.old", "db.sqlite3.ol2")
        except FileNotFoundError:
            pass
        # (db) -> old
        shutil.copyfile("db.sqlite3", "db.sqlite3.old")


        # Because Django 2.0+ now enforces FK checks for Sqlite DBs, if we are missing migrations that would now involve
        # FK checks we have a serious problem - We can't apply the migrations until the DB is fixed, and we can't fix
        # the DB until we apply the migrations. The solution is to apply the migrations with FK checks disabled, then
        # run this script to fix the database. I've created a management command - `migrate_no_fk` - which can handle
        # the migration. Let's call that now just to ensure that we're in the right state.
        execute_from_command_line(['manage.py', 'migrate_no_fk'])

        # Everything should be migrated at this point - Let's continue.

        # There was some kind of an issue with firmware data specifically - let's delete it all just to be safe
        try:
            self.clear_firmware_data()
        except:
            print("Unable to clear data!!")


        # Once that's done, we're going to attempt to loop over all the apps/models and rebuild everything just to be
        # safe.
        for app in apps.get_app_configs():
            print("Rebuilding app {}...".format(app.verbose_name))
            for model in app.get_models(include_auto_created=True):
                if model._meta.managed and not (model._meta.proxy or model._meta.swapped):
                    for base in model.__bases__:
                        if hasattr(base, '_meta'):
                            base._meta.local_many_to_many = []
                    model._meta.local_many_to_many = []
                    with connection.schema_editor() as editor:
                        try:
                            constraint_check = connection.disable_constraint_checking()
                        except:
                            connection.connection = connection.connect()
                            constraint_check = connection.disable_constraint_checking()
                        print("Rebuilding model {}".format(model))
                        editor._remake_table(model)
        print("Completed app rebuilding - running check_constraints to ensure we're in a consistent state.")
        connection.check_constraints()
        config.SQLITE_OK_DJANGO_2 = True
        print("Rebuild complete!")
        return True

    def handle(self, *args, **options):
        self.fix_sqlite_for_django_2()
