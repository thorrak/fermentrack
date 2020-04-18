from __future__ import with_statement

from django.core.management.base import BaseCommand  # , CommandError

from django.apps import apps
from django.db import connection
from constance import config


class Command(BaseCommand):
    help = "Fixes SQLite databases that have been migrated from Django 1.x to Django 2.0+"

    def fix_sqlite_for_django_2(self):
        for app in apps.get_app_configs():
            for model in app.get_models(include_auto_created=True):
                if model._meta.managed and not (model._meta.proxy or model._meta.swapped):
                    for base in model.__bases__:
                        if hasattr(base, '_meta'):
                            base._meta.local_many_to_many = []
                    model._meta.local_many_to_many = []
                    with connection.schema_editor() as editor:
                        editor._remake_table(model)
        config.SQLITE_OK_DJANGO_2 = True
        return True

    def handle(self, *args, **options):
        self.fix_sqlite_for_django_2()
