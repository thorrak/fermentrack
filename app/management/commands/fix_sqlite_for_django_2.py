from __future__ import with_statement

from django.core.management.base import BaseCommand  # , CommandError

from django.apps import apps
from django.db import connection
from constance import config
import shutil

import django.db.utils


class Command(BaseCommand):
    help = "Fixes SQLite databases that have been migrated from Django 1.x to Django 2.0+"

    def fix_sqlite_for_django_2(self):


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

        # First thing's first - We want to find any broken foreign key checks, and rebuild those tables specifically
        fixed_tables = []
        fk_violations = connection.cursor().execute('PRAGMA foreign_key_check').fetchall()
        # See https://www.sqlite.org/pragma.html#pragma_foreign_key_check
        for table_name, rowid, referenced_table_name, foreign_key_index in fk_violations:
            for app in apps.get_app_configs():
                for model in app.get_models(include_auto_created=True):
                    if model._meta.managed and not (model._meta.proxy or model._meta.swapped):
                        if model._meta.db_table == table_name:
                            # What we're trying to do is check every model in every app to see if the table that holds
                            # it is the table with the broken foreign key
                            with connection.schema_editor() as editor:
                                if table_name not in fixed_tables:
                                    print("Table {} has a foreign key issue referencing table {} - Attempting to fix...".format(table_name, referenced_table_name))
                                    try:
                                        constraint_check = connection.disable_constraint_checking()
                                    except:
                                        connection.connection = connection.connect()
                                        constraint_check = connection.disable_constraint_checking()
                                    editor._remake_table(model)
                                    fixed_tables.append(table_name)
            if table_name not in fixed_tables:
                print("Unable to locate suitable model referencing table {}. Stopping.".format(table_name))
                raise django.db.utils.IntegrityError("fix_sqlite_for_django_2 unable to find suitable model referencing table {}".format(table_name))

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
                        print("Rebuilding model {} - FK Check Disabled: {}".format(model, constraint_check))
                        editor._remake_table(model)
        connection.check_constraints()
        config.SQLITE_OK_DJANGO_2 = True
        return True

    def handle(self, *args, **options):
        self.fix_sqlite_for_django_2()
