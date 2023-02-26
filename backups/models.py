import shlex
import subprocess

from django.db import models
import django.core.management
from django.apps import apps
from django.core.management.commands import dumpdata
from django.utils.translation import gettext_lazy as _

from django.db import DEFAULT_DB_ALIAS
from django.conf import settings
from model_utils.models import TimeStampedModel
from django.utils import timezone
import os
import tarfile
import tarsafe  # Provides safer extract functions
from django.db.models.signals import post_delete
from django.dispatch import receiver
from pathlib import Path


def default_filename_prefix():
    return timezone.now().strftime('%Y-%m-%dT%H.%M.%S')


class Backup(TimeStampedModel):
    class Meta:
        permissions = [
            ("restore_backup", "Can restore from a backup (which can overwrite all data in Fermentrack)"),
        ]

    filename_prefix = models.CharField(max_length=128, default=default_filename_prefix,
                                       help_text=_("The filename prefix for this backup's archive"))

    def __str__(self):
        return self.filename_prefix

    @staticmethod
    def get_unmanaged_models() -> list:
        app_list = dict.fromkeys(
            app_config for app_config in apps.get_app_configs()
            if app_config.models_module is not None
        )

        models = []

        for (app_config, model_list) in app_list.items():
            # if model_list is None:
            models.extend(app_config.get_models())
            # else:
            #     models.extend(model_list)

        excluded_models = []
        for model in models:
            if not model._meta.managed:
                excluded_models.append(model._meta.label)

        return excluded_models

    @classmethod
    def get_exclude_list(cls) -> list:
        excluded_models = cls.get_unmanaged_models()
        return excluded_models + settings.BACKUPS_EXCLUDE_APPS

    @classmethod
    def dump_database_to_file(cls):
        data_dump_file = settings.BACKUP_STAGING_DIR / settings.BACKUP_DATA_DUMP_FILE_NAME

        exclude_models = cls.get_exclude_list()

        options = {
            'format': 'json',
            'indent': '  ',
            'exclude': exclude_models,
            'output': str(data_dump_file),  # Convert back from path to string
            'database': DEFAULT_DB_ALIAS,
            'traceback': True,
            'use_natural_foreign_keys': False,
            'use_natural_primary_keys': False,
            'use_base_manager': False,
            'primary_keys': None,
            'verbosity': 0,
        }

        cmd = dumpdata.Command()
        cmd.handle(*[], **options)

    @property
    def outfile_path(self) -> Path:
        return settings.BACKUP_STAGING_DIR.parent / (self.filename_prefix + ".tar.xz")

    def compress_staging_to_file(self):
        data_dump_file = settings.BACKUP_STAGING_DIR / settings.BACKUP_DATA_DUMP_FILE_NAME
        with tarfile.open(self.outfile_path, mode="w:xz") as f:
            f.add(data_dump_file, arcname=settings.BACKUP_DATA_DUMP_FILE_NAME)
            # f.add(settings.MEDIA_ROOT, arcname="media/")
            f.add(settings.DATA_ROOT, arcname="data/")

    def perform_backup(self):
        self.dump_database_to_file()
        self.compress_staging_to_file()

    def decompress_backup_file(self):
        data_dump_file = settings.BACKUP_STAGING_DIR / settings.BACKUP_DATA_DUMP_FILE_NAME

        with tarsafe.open(self.outfile_path, mode="r:*") as f:
            f.extractall(path=settings.ROOT_DIR)

    def load_database_from_file(self):
        data_dump_file = settings.ROOT_DIR / settings.BACKUP_DATA_DUMP_FILE_NAME
        django.core.management.call_command('loaddata', data_dump_file)

    def perform_restore(self):
        self.decompress_backup_file()
        self.load_database_from_file()


@receiver(post_delete, sender=Backup)
def backup_delete(sender, instance, **kwargs):
    # When a Backup is deleted, also delete the backup file
    instance.outfile_path.unlink(missing_ok=True)
