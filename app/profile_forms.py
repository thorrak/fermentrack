from django import forms
from app.models import FermentationProfile, FermentationProfilePoint
from django.core import validators
import fermentrack_django.settings as settings

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


class FermentationProfilePointForm(forms.Form):
    ttl = forms.CharField(help_text="Time from the start of fermentation at which the temperature will be reached. " +
                                    "(Example: 7d 3h 15m 4s)",
                          widget=forms.TextInput(attrs={'placeholder': 'Ex: 7d 3h 15m 4s'}),
                          validators=[validators.RegexValidator(regex="([0-9]+[ ]*[ywdhms]{1}[ ]*)+",
                                                                message="Invalid TTL format")])
    temperature_setting = forms.DecimalField(min_value=-20, max_value=212, max_digits=5, decimal_places=2,
                                             widget=forms.TextInput(
                                                 attrs={'placeholder': 'Ex: 35'}),
                                             help_text="Temperature goal when TTL is reached")

    # Check that the ttl format is valid, and if it is, replace it with a datetime delta object
    def clean_ttl(self):
        if 'ttl' in self.cleaned_data:
            ttl_text = self.cleaned_data['ttl']
        else:
            return None

        if len(ttl_text) <= 1:
            return None

        return FermentationProfilePoint.string_to_ttl(ttl_text)


class FermentationProfileImportForm(forms.Form):

    placeholder_profile = """Example:
====================================
| Sample Profile                   |
| Standard Profile                 |
====================================
| 7d    | 68.00 F                  |
| 10d   | 72.00 F                  |
| 15d   | 35.00 F                  |
===================================="""

    import_text = forms.CharField(widget=forms.Textarea(attrs={'style': "font-family:monospace; font-size:11pt;", 'wrap': 'off',
                                                               'placeholder': placeholder_profile}),
                                  help_text="The text of the exported profile")


class FermentationProfileCopyForm(forms.Form):
    new_profile_name = forms.CharField(help_text="The text of the exported profile", max_length=128)


class FermentationProfileRenameForm(forms.Form):
    profile_name = forms.CharField(help_text="The new name for the profile", max_length=128)