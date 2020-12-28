from django import forms

from external_push.models import GenericPushTarget, BrewersFriendPushTarget, BrewfatherPushTarget, ThingSpeakPushTarget, GrainfatherPushTarget
from django.core import validators
import fermentrack_django.settings as settings

from django.forms import ModelForm


class GenericPushTargetModelForm(ModelForm):
    class Meta:
        model = GenericPushTarget
        fields = ['name', 'push_frequency', 'api_key', 'brewpi_push_selection', 'brewpi_to_push',
                  'gravity_push_selection', 'gravity_sensors_to_push', 'target_host', 'target_port']


class BrewersFriendPushTargetModelForm(ModelForm):
    class Meta:
        model = BrewersFriendPushTarget
        fields = ['gravity_sensor_to_push', 'push_frequency', 'api_key']


class BrewfatherPushTargetModelForm(ModelForm):
    class Meta:
        model = BrewfatherPushTarget
        fields = ['gravity_sensor_to_push', 'push_frequency', 'logging_url', 'device_type', 'brewpi_to_push']


class ThingSpeakPushTargetModelForm(ModelForm):
    class Meta:
        model = ThingSpeakPushTarget
        fields = ['name', 'push_frequency', 'api_key', 'brewpi_to_push']


class GrainfatherPushTargetModelForm(ModelForm):
    class Meta:
        model = GrainfatherPushTarget
        fields = ['gravity_sensor_to_push', 'push_frequency', 'logging_url', 'gf_name']
