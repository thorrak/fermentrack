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
        # tz = pytz.timezone(getattr(settings, 'TIME_ZONE', False))
        ttl_text = self.cleaned_data['ttl']

        # Split out the d/h/m/s of the timer
        try:
            timer_pattern = r"(?P<time_amt>[0-9]+)[ ]*(?P<ywdhms>[ywdhms]{1})"
            timer_regex = re.compile(timer_pattern)
            timer_matches = timer_regex.finditer(ttl_text)
        except:
            raise forms.ValidationError("TTL format is invalid")


        # timer_time is equal to now + the time delta
        time_delta = datetime.timedelta(seconds=0)
        for this_match in timer_matches:
            dhms = this_match.group('ywdhms')
            delta_amt = int(this_match.group('time_amt'))
            if dhms == 'y':  # This doesn't account for leap years, but whatever.
                time_delta = time_delta + datetime.timedelta(days=(365*delta_amt))
            elif dhms == 'w':
                time_delta = time_delta + datetime.timedelta(weeks=delta_amt)
            elif dhms == 'd':
                time_delta = time_delta + datetime.timedelta(days=delta_amt)
            elif dhms == 'h':
                time_delta = time_delta + datetime.timedelta(hours=delta_amt)
            elif dhms == 'm':
                time_delta = time_delta + datetime.timedelta(minutes=delta_amt)
            elif dhms == 's':
                time_delta = time_delta + datetime.timedelta(seconds=delta_amt)

        # return self.cleaned_data['ttl']
        return time_delta