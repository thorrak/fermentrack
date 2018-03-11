from __future__ import unicode_literals

from django.apps import AppConfig


class GravityAppConfig(AppConfig):
    name = 'gravity'

    def ready(self):
        from . import signals
