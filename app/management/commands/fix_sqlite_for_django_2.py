from __future__ import with_statement

from django.core.management.base import BaseCommand  # , CommandError

from django.apps import apps
from django.db import connection
from constance import config
import shutil

from django.db import utils


class Command(BaseCommand):
    help = "Fixes SQLite databases that have been migrated from Django 1.x to Django 2.0+"

    def fix_sqlite_for_django_2(self):

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

        for app in apps.get_app_configs():
            print("Fixing app {}...".format(app.verbose_name))
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
                        print("Rebuilding model {} - FK Check {}".format(model, constraint_check))
                        try:
                            editor._remake_table(model)
                        except utils.IntegrityError:
                            # Foreign key check fails during rebuild
                            pass
        connection.check_constraints()
        config.SQLITE_OK_DJANGO_2 = True
        return True

    def handle(self, *args, **options):
        self.fix_sqlite_for_django_2()
