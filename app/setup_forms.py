from django.contrib.auth.models import User
from django import forms
from constance import config
#from constance.admin import ConstanceForm
from django.conf import settings


###################################################################################################################
# Initial Setup Forms
###################################################################################################################


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
        ('true', 'Yes - Require Login'),
        ('false', 'No - Can be seen without logging in')
    ]

    # Fields for our form, the initial value taken from configuration.

    # There appears to be a bug with constance where if you use config in a form setup it will die if the constance
    # database table hasn't been created yet (ie - at initial setup)
    brewery_name = forms.CharField()  # initial=config.BREWERY_NAME
    date_time_format = forms.ChoiceField(  # initial=config.DATE_TIME_FORMAT
        choices=date_time_format_select_choices,
        )
    date_time_format_display = forms.ChoiceField(  # initial=config.DATE_TIME_FORMAT_DISPLAY
        choices=date_time_display_select_choices,
        )
    require_login_for_dashboard = forms.ChoiceField(  # initial=config.REQUIRE_LOGIN_FOR_DASHBOARD
        choices=true_false,
        # widget=forms.RadioSelect(),
        )
    temperature_format = forms.ChoiceField(  # initial=config.TEMPERATURE_FORMAT
        choices=temperature_format_select_choices,
        )

    def __init__(self, *args, **kwargs):
        super(GuidedSetupConfigForm, self).__init__(*args, **kwargs)
        for this_field in self.fields:
            self.fields[this_field].widget.attrs['class'] = "form-control"

        self.fields['brewery_name'].initial = config.BREWERY_NAME
        self.fields['brewery_name'].help_text = config.BREWERY_NAME
        self.fields['date_time_format'].initial = config.DATE_TIME_FORMAT
        self.fields['date_time_format_display'].initial = config.DATE_TIME_FORMAT_DISPLAY
        self.fields['require_login_for_dashboard'].initial = config.REQUIRE_LOGIN_FOR_DASHBOARD
        self.fields['temperature_format'].initial = config.TEMPERATURE_FORMAT

        # This is super-hackish, but whatever. If it works, it works
        for this_field in self.fields:
            try:
                default_value, help_text, data_type = settings.CONSTANCE_CONFIG[this_field.upper()]
                self.fields[this_field].help_text = help_text
            except:
                pass


###################################################################################################################
# Guided Setup Forms
###################################################################################################################


class GuidedDeviceSelectForm(forms.Form):
    DEVICE_FAMILY_CHOICES = (
        ('ESP8266', 'ESP8266'),
        ('Arduino', 'Arduino (and compatible)'),
        ('Spark', 'Spark Core'),
        ('Fuscus', 'Native Python (Fuscus)'),
    )

    device_family = forms.ChoiceField(label="Device Family",
                                      widget=forms.Select(attrs={'class': 'form-control',
                                                                 'data-toggle': 'select'}),
                                      choices=DEVICE_FAMILY_CHOICES, required=True)


class GuidedDeviceFlashForm(forms.Form):
    DEVICE_FAMILY_CHOICES = GuidedDeviceSelectForm.DEVICE_FAMILY_CHOICES

    device_family = forms.ChoiceField(label="Device Family",
                                      widget=forms.Select(attrs={'class': 'form-control',
                                                                 'data-toggle': 'select'}),
                                      choices=DEVICE_FAMILY_CHOICES, required=True)
    should_flash_device = forms.BooleanField(widget=forms.HiddenInput, required=False, initial=False)


