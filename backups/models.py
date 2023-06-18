import json
import shlex
import shutil
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

from app.models import Beer
from backups import backup_funcs, restore_funcs
from gravity.models import GravityLog

BACKUP_FILE_VERSION = "2.0.0"

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
    def generate_backup_dict(cls):
        backup_dict = {
            'file_version': BACKUP_FILE_VERSION,
            'fermentrack_options': backup_funcs.dump_fermentrack_configuration_options(),

            'brewpi_devices': backup_funcs.dump_brewpi_devices(),
            'beers': backup_funcs.dump_beers(),
            'profiles': backup_funcs.dump_fermentation_profiles(),

            'gravity_sensors': backup_funcs.dump_gravity_sensors(),
            'gravity_logs': backup_funcs.dump_gravity_logs(),
            'tiltbridges': backup_funcs.dump_tiltbridges(),
            'tilts': backup_funcs.dump_tilt_configurations(),
            'tilt_temp_calibration_points': backup_funcs.dump_tilt_temp_calibration_points(),
            'tilt_gravity_calibration_points': backup_funcs.dump_tilt_gravity_calibration_points(),
            'ispindels': backup_funcs.dump_ispindel_configurations(),
            'ispindel_gravity_calibration_points': backup_funcs.dump_ispindel_gravity_calibration_points(),
        }
        return backup_dict

    @classmethod
    def generate_backup_json(cls):
        backup_dict = cls.generate_backup_dict()
        return json.dumps(backup_dict)

    @classmethod
    def write_backup_to_file(cls):
        """Write the JSON from generate_backup_json to a file"""
        data_dump_file = settings.BACKUP_STAGING_DIR / settings.BACKUP_DATA_DUMP_FILE_NAME
        with open(data_dump_file, "w") as f:
            f.write(cls.generate_backup_json())

    @classmethod
    def add_logs_to_file(cls, t_cls, f: tarfile.TarFile, arc_prefix:str="data/"):
        """Add all the log files associated with GravityLog objects to the tarfile, changing their name to match the
         UUID of the GravityLog object"""
        log_types = ['base_csv', 'full_csv','annotation_json']
        file_name_base = settings.ROOT_DIR / settings.DATA_ROOT

        # Loop through each of the three log types for each of the beer objects, and add the CSV file to the tarfile
        for obj in t_cls.objects.all():
            for log_type in log_types:
                csv_path = file_name_base / obj.full_filename(log_type)
                if os.path.isfile(csv_path):
                    f.add(csv_path, arcname=f"{arc_prefix}{obj.uuid}_{log_type}.csv")


    @property
    def outfile_path(self) -> Path:
        return settings.BACKUP_STAGING_DIR.parent / (self.filename_prefix + ".tar.xz")

    def compress_staging_to_file(self):
        data_dump_file = settings.BACKUP_STAGING_DIR / settings.BACKUP_DATA_DUMP_FILE_NAME
        with tarfile.open(self.outfile_path, mode="w:xz") as f:
            f.add(data_dump_file, arcname=settings.BACKUP_DATA_DUMP_FILE_NAME)
            # f.add(settings.MEDIA_ROOT, arcname="media/")
            # f.add(settings.DATA_ROOT, arcname="data/")
            self.add_logs_to_file(Beer, f, arc_prefix="data/")
            self.add_logs_to_file(GravityLog, f, arc_prefix="data/")

    def perform_backup(self):
        self.write_backup_to_file()
        self.compress_staging_to_file()

    def decompress_backup_file(self):
        """Decompress the backup file to the staging directory"""
        with tarsafe.open(self.outfile_path, mode="r:*") as f:
            f.extractall(settings.BACKUP_STAGING_DIR)

    # The next function is the "legacy" loader, which is used for backups created when the django core management
    # commands were used to create the backup.
    @staticmethod
    def load_legacy_database_from_file():
        data_dump_file = settings.ROOT_DIR / settings.BACKUP_DATA_DUMP_FILE_NAME
        django.core.management.call_command('loaddata', data_dump_file)

    @staticmethod
    def restore_log_files():
        """Restore the log files from the backup"""
        backup_root = settings.BACKUP_STAGING_DIR / "data"
        for cls in [Beer, GravityLog]:
            for obj in cls.objects.all():
                for log_type in ['base_csv', 'full_csv', 'annotation_json']:
                    if Backup.is_legacy():
                        csv_path = backup_root / obj.full_filename(log_type)
                    else:
                        csv_path = backup_root / f"{obj.uuid}_{log_type}.csv"
                    if os.path.isfile(csv_path):
                        shutil.copy(csv_path, settings.ROOT_DIR / settings.DATA_ROOT / obj.full_filename(log_type))

    def load_database_from_file(self):
        data_dump_file = settings.ROOT_DIR / settings.BACKUP_DATA_DUMP_FILE_NAME
        update = True  # Hardcoding this for now, but eventually we'll want to make this a user option

        # Load the JSON
        with open(data_dump_file, "r") as data_dump_file:
            backup_dict = json.load(data_dump_file)

        # Load the data from the backup file. Note that the order matters here.
        restore_result = {}
        if 'fermentrack_options' in backup_dict:
            restore_result['fermentrack_options'] = restore_funcs.restore_fermentrack_configuration_options(
                backup_dict['fermentrack_options'])

        if 'brewpi_devices' in backup_dict:
            restore_result['brewpi_devices'] = restore_funcs.restore_brewpi_devices(backup_dict['brewpi_devices'],
                                                                                    update=update)
        if 'beers' in backup_dict:
            restore_result['beers'] = restore_funcs.restore_beers(backup_dict['beers'], update=update)
        if 'profiles' in backup_dict:
            restore_result['profiles'] = restore_funcs.restore_fermentation_profiles(backup_dict['profiles'],
                                                                                     update=update)
        if 'gravity_sensors' in backup_dict:
            restore_result['gravity_sensors'] = restore_funcs.restore_gravity_sensors(backup_dict['gravity_sensors'],
                                                                                      update=update)
        if 'gravity_logs' in backup_dict:
            restore_result['gravity_logs'] = restore_funcs.restore_gravity_logs(backup_dict['gravity_logs'],
                                                                                update=update)
        if 'tiltbridges' in backup_dict:
            restore_result['tiltbridges'] = restore_funcs.restore_tiltbridges(backup_dict['tiltbridges'], update=update)
        if 'tilts' in backup_dict:
            restore_result['tilts'] = restore_funcs.restore_tilt_configurations(backup_dict['tilts'], update=update)
        if 'tilt_temp_calibration_points' in backup_dict:
            restore_result['tilt_temp_calibration_points'] = restore_funcs.restore_tilt_temp_calibration_points(
                backup_dict['tilt_temp_calibration_points'], update=update)
        if 'tilt_gravity_calibration_points' in backup_dict:
            restore_result['tilt_gravity_calibration_points'] = restore_funcs.restore_tilt_gravity_calibration_points(
                backup_dict['tilt_gravity_calibration_points'], update=update)
        if 'ispindels' in backup_dict:
            restore_result['ispindels'] = restore_funcs.restore_ispindel_configurations(backup_dict['ispindels'],
                                                                                        update=update)
        if 'ispindel_gravity_calibration_points' in backup_dict:
            restore_result['ispindel_gravity_calibration_points'] = \
                restore_funcs.restore_ispindel_gravity_calibration_points(
                    backup_dict['ispindel_gravity_calibration_points'], update=update)



    @staticmethod
    def get_backup_file_version(file_path) -> str:
        """Get the version of the backup file"""
        with open(file_path, "r") as data_dump_file:
            backup_dict = json.load(data_dump_file)
            if 'file_version' not in backup_dict:
                return "1.0.0"  # If the file version is not present, assume it's 1.0.0 (which is "Legacy")
            return backup_dict['file_version']

    @staticmethod
    def is_legacy() -> bool:
        """Return True if the backup file is a legacy backup"""
        return Backup.get_backup_file_version(settings.BACKUP_STAGING_DIR / settings.BACKUP_DATA_DUMP_FILE_NAME) == "1.0.0"

    def perform_restore(self):
        self.decompress_backup_file()
        if self.is_legacy():
            # This is a legacy backup. Call the legacy loader
            self.load_legacy_database_from_file()
        else:
            # This is a current backup. Call the current loader
            self.load_database_from_file()
        self.restore_log_files()

@receiver(post_delete, sender=Backup)
def backup_delete(sender, instance, **kwargs):
    # When a Backup is deleted, also delete the backup file
    instance.outfile_path.unlink(missing_ok=True)
