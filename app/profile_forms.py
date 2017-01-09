from django import forms
from app.models import FermentationProfile, FermentationProfilePoint
from django.core import validators
import brewpi_django.settings as settings

from django.forms import ModelForm

import re
import datetime
import pytz


# For the actual fermentation profile points, we're going to do something more complex. For the overriding
# FermentationProfile object, however, let's just use a model form.
class FermentationProfileForm(ModelForm):
    class Meta:
        model = FermentationProfile
        fields = ['name']

    def __init__(self, *args, **kwargs):
        super(FermentationProfileForm, self).__init__(*args, **kwargs)
        for this_field in self.fields:
            self.fields[this_field].widget.attrs['class'] = "form-control"
