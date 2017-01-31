from django.contrib.auth.models import User
from django import forms
from constance import config
from constance.admin import ConstanceForm
from django.conf import settings

class GuidedSetupUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'password')

class GuidedSetupConfigForm(forms.Form):
    # Get choices from CONSTANCE_ADDITIONAL_FIELDS setting
    date_time_format_select_choices = settings.CONSTANCE_ADDITIONAL_FIELDS['date_time_format_select'][1]['choices']
    date_time_display_select_choices = settings.CONSTANCE_ADDITIONAL_FIELDS['date_time_display_select'][1]['choices']
    temperature_format_select_choices = settings.CONSTANCE_ADDITIONAL_FIELDS['temperature_format_select'][1]['choices']
    true_false = [
        ('true', 'true'),
        ('false', 'false')
    ]
    # Fields for our form, the initial value taken from configuration.
    brewery_name = forms.CharField(initial=config.BREWERY_NAME)
    date_time_format = forms.ChoiceField(
        choices=date_time_format_select_choices,
        initial=config.DATE_TIME_FORMAT
        )
    date_time_format_display = forms.ChoiceField(
        choices=date_time_display_select_choices,
        initial=config.DATE_TIME_FORMAT_DISPLAY
        )
    require_login_for_dashboard = forms.ChoiceField(
        choices=true_false,
        widget=forms.RadioSelect(),
        initial=config.REQUIRE_LOGIN_FOR_DASHBOARD
        )
    temperature_format = forms.ChoiceField(
        choices=temperature_format_select_choices,
        initial=config.TEMPERATURE_FORMAT
        )
