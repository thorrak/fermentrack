from __future__ import with_statement

from django.core.management.base import BaseCommand  # , CommandError

import backups.models


class Command(BaseCommand):
    help = "Generates a backup file manually that can be restored to another instance of Fermentrack"

    def generate_backup(self):
        backup_obj = backups.models.Backup()
        backup_obj.perform_backup()

        print("Done generating backup")
        print(f"File saved at: {backup_obj.outfile_path}")

        backup_obj.save()

    def handle(self, *args, **options):
        self.generate_backup()
