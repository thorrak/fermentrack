from django import forms

from external_push.models import GenericPushTarget, BrewersFriendPushTarget
from django.core import validators
import fermentrack_django.settings as settings

from django.forms import ModelForm


class GenericPushTargetModelForm(ModelForm):
    class Meta:
        model = GenericPushTarget
        fields = ['name', 'push_frequency', 'api_key', 'brewpi_push_selection', 'brewpi_to_push',
                  'gravity_push_selection', 'gravity_sensors_to_push', 'target_type', 'target_host', 'target_port']


class BrewersFriendPushTargetModelForm(ModelForm):
    class Meta:
        model = BrewersFriendPushTarget
        fields = ['gravity_sensor_to_push', 'push_frequency', 'api_key']



