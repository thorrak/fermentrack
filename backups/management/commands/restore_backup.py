import tarfile

from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand  # , CommandError
import backups.models
from pathlib import Path
import shutil


def is_valid_file(parser, arg):
    p = Path(arg)

    if not p.exists():
        parser.error("The file %s does not exist!" % p)
    elif len(p.suffixes) < 2 or p.suffixes[-1] != ".xz" or p.suffixes[-2] != ".tar":
        parser.error("The file %s must be a .tar.xz file!" % p.name)
    elif len(p.name) <= 6:
        parser.error("The file %s must have a filename before .tar.xz!" % p.name)
    return p


class Command(BaseCommand):
    help = 'Restores the specified backup file'

    def add_arguments(self, parser):
        # parser.add_argument('backup_archive', nargs='+', type=int)

        parser.add_argument(dest="filename",
                            help="Backup archive", metavar="FILE",
                            type=lambda x: is_valid_file(parser, x))

    def handle(self, *args, **options):
        backup_prefix = str(options['filename'])[:-7]
        print(f"Backup prefix: {backup_prefix}")

        # If we already have a backup with this prefix, we don't want to override it. Print an error and kick back.
        try:
            backup_obj = backups.models.Backup.objects.get(filename_prefix=backup_prefix)
            print(f"Backup object {backup_prefix} already exists. Please rename the file and attempt to restore again.")
        except ObjectDoesNotExist:
            pass

        # Otherwise, create the backup object, copy the file to the backup staging area, and perform the restore
        backup_obj = backups.models.Backup(filename_prefix=backup_prefix)
        shutil.copy(options['filename'], backup_obj.outfile_path)
        backup_obj.save()
        try:
            backup_obj.perform_restore()
        except tarfile.ReadError:
            # Tarfile was unable to extract the archive
            print("Unable to read backup file. Not a valid archive.")

        print("Done restoring backup")
