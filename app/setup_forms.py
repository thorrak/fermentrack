from django.contrib.auth.models import User
from django import forms
from constance import config
#from constance.admin import ConstanceForm
from django.conf import settings
import pytz


###################################################################################################################
# Initial Setup Forms
###################################################################################################################


class GuidedSetupUserForm(forms.ModelForm):
    """
    GuidedSetupUserForm presents a user with a simple form, with two fields for
    password and upon save validates that the passwords match.
    """
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Password (again)", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('username', 'email')

    def clean_password2(self):
        """Here we actually validate so that the passwords matches"""
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError("The two password fields didn't match.")
        return password2

    def save(self, commit=True):
        """Saves the new matched validated password"""
        user = super(GuidedSetupUserForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class GuidedSetupConfigForm(forms.Form):
    # Get choices from CONSTANCE_ADDITIONAL_FIELDS setting
    date_time_display_select_choices = settings.CONSTANCE_ADDITIONAL_FIELDS['date_time_display_select'][1]['choices']
    temperature_format_select_choices = settings.CONSTANCE_ADDITIONAL_FIELDS['temperature_format_select'][1]['choices']
    gravity_display_format_select_choices = settings.CONSTANCE_ADDITIONAL_FIELDS['gravity_display_format_select'][1]['choices']
    login_true_false = [
        (True, 'Yes - Require Login'),
        (False, 'No - Can be seen without logging in')
    ]

    true_false =[
        (True, 'Yes'),
        (False, 'No')
    ]
    theme_select = settings.CONSTANCE_ADDITIONAL_FIELDS['theme_select'][1]['choices']

    update_options = settings.CONSTANCE_ADDITIONAL_FIELDS['git_update_type_select'][1]['choices'][1:]

    # Fields for our form, the initial value taken from configuration.

    # There appears to be a bug with constance where if you use config in a form setup it will die if the constance
    # database table hasn't been created yet (ie - at initial setup)
    brewery_name = forms.CharField()  # initial=config.BREWERY_NAME

    custom_theme = forms.ChoiceField(
        choices=theme_select,
        )

    date_time_format_display = forms.ChoiceField(  # initial=config.DATE_TIME_FORMAT_DISPLAY
        choices=date_time_display_select_choices,
        )

    require_login_for_dashboard = forms.ChoiceField(  # initial=config.REQUIRE_LOGIN_FOR_DASHBOARD
        choices=login_true_false,
        # widget=forms.RadioSelect(),
        )

    temperature_format = forms.ChoiceField(  # initial=config.TEMPERATURE_FORMAT
        choices=temperature_format_select_choices,
        )

    gravity_display_format = forms.ChoiceField(  # initial=config.GRAVITY_DISPLAY_FORMAT
        choices=gravity_display_format_select_choices,
        )

    preferred_timezone = forms.ChoiceField(
        choices=[(x,x) for x in pytz.common_timezones]
    )

    enable_gravity_support = forms.ChoiceField(  # initial=config.GRAVITY_SUPPORT_ENABLED
        choices=true_false,
        # widget=forms.RadioSelect(),
        )

    update_preference = forms.ChoiceField(  # initial=config.GRAVITY_SUPPORT_ENABLED
        choices=update_options,
        help_text="What type of updates would you like to receive for Fermentrack?"
        # widget=forms.RadioSelect(),
        )

    enable_sentry_support = forms.ChoiceField(  # initial=settings.ENABLE_SENTRY
        choices=true_false,
        help_text="Enable automatic error reporting to Fermentrack developers",
        # widget=forms.RadioSelect(),
        )

    def __init__(self, *args, **kwargs):
        super(GuidedSetupConfigForm, self).__init__(*args, **kwargs)
        for this_field in self.fields:
            self.fields[this_field].widget.attrs['class'] = "form-control"

        self.fields['brewery_name'].initial = config.BREWERY_NAME
        self.fields['brewery_name'].help_text = config.BREWERY_NAME
        self.fields['custom_theme'].initial = config.CUSTOM_THEME
        self.fields['date_time_format_display'].initial = config.DATE_TIME_FORMAT_DISPLAY
        self.fields['require_login_for_dashboard'].initial = config.REQUIRE_LOGIN_FOR_DASHBOARD
        self.fields['temperature_format'].initial = config.TEMPERATURE_FORMAT
        self.fields['preferred_timezone'].initial = config.PREFERRED_TIMEZONE
        self.fields['enable_gravity_support'].initial = config.GRAVITY_SUPPORT_ENABLED
        self.fields['update_preference'].initial = config.GIT_UPDATE_TYPE
        self.fields['gravity_display_format'].initial = config.GRAVITY_DISPLAY_FORMAT
        self.fields['enable_sentry_support'].initial = settings.ENABLE_SENTRY

        # This is super-hackish, but whatever. If it works, it works
        for this_field in self.fields:
            try:
                default_value, help_text, data_type = settings.CONSTANCE_CONFIG[this_field.upper()]
                self.fields[this_field].help_text = help_text
            except:
                pass

    def clean_enable_sentry_support(self):
        enabled = self.cleaned_data.get('enable_sentry_support')

        if enabled == 'True':
            return True
        elif enabled == 'False':
            return False
        else:
            raise forms.ValidationError("Must be either True or False (Yes or No)")

    def clean_enable_gravity_support(self):
        enabled = self.cleaned_data.get('enable_gravity_support')

        if enabled == 'True':
            return True
        elif enabled == 'False':
            return False
        else:
            raise forms.ValidationError("Must be either True or False (Yes or No)")

    def clean_require_login_for_dashboard(self):
        enabled = self.cleaned_data.get('require_login_for_dashboard')

        if enabled == 'True':
            return True
        elif enabled == 'False':
            return False
        else:
            raise forms.ValidationError("Must be either True or False (Yes or No)")




###################################################################################################################
# Guided Setup Forms
###################################################################################################################


class GuidedDeviceSelectForm(forms.Form):
    DEVICE_FAMILY_CHOICES = (
        ('ESP8266', 'ESP8266'),
        ('Arduino', 'Arduino Uno (and compatible)'),  # TODO - Add Leonardo support
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


