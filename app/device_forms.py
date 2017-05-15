from django import forms
from app.models import BrewPiDevice, OldControlConstants, NewControlConstants, SensorDevice, FermentationProfile
from django.core import validators
import fermentrack_django.settings as settings

from django.forms import ModelForm

import re
import datetime
import pytz
import random

class DeviceForm(forms.Form):

    device_name = forms.CharField(max_length=48, help_text="Unique name for this device",
                                  widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Device Name'}))

    temp_format = forms.ChoiceField(choices=BrewPiDevice.TEMP_FORMAT_CHOICES, initial='C', help_text="Temperature units",
                                    widget=forms.Select(attrs={'class': 'form-control'}))

    data_point_log_interval = forms.ChoiceField(initial=30, choices=BrewPiDevice.DATA_POINT_TIME_CHOICES,
                                                help_text="Time between logged data points",
                                                widget=forms.Select(attrs={'class': 'form-control'}))

    connection_type = forms.ChoiceField(initial='serial', choices=BrewPiDevice.CONNECTION_TYPE_CHOICES,
                                        help_text="Type of connection between the Raspberry Pi and the hardware",
                                        widget=forms.Select(attrs={'class': 'form-control'}))


    useInetSocket = forms.BooleanField(required=False, initial=True,
                                       help_text="Whether or not to use an internet socket (rather than local)")

    # Note - initial=random.randint(2000,3000) only assigns at Fermentrack load-time, not when the form is instantiated
    # There is code on the forms which will effectively accomplish the same thing every time the user accesses the form
    socketPort = forms.IntegerField(initial=random.randint(2000,3000), min_value=1024, max_value=65536, required=False,
                                    help_text="The socket port to use, this needs to be unique per fermentrack device",
                                    widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 1234'}))

    socketHost = forms.CharField(max_length=128, initial="localhost", required=False,
                                 help_text="The ip or a hostname on the local machine for the fermentrack controller script will bind to",
                                 widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: localhost'}))

    serial_port = forms.CharField(max_length=255, initial="auto", required=False,
                                  help_text="Serial port to which the BrewPi device is connected (Only used if " +
                                            "connection_type is serial)",
                                  widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'auto'}))

    serial_alt_port = forms.CharField(max_length=255, initial="None", required=False,
                                      help_text="Alternate serial port path (Only used if connection_type is serial)",
                                      widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'None'}))

    board_type = forms.ChoiceField(initial="uno", choices=BrewPiDevice.BOARD_TYPE_CHOICES,
                                   help_text="Board type to which BrewPi is connected",
                                   widget=forms.Select(attrs={'class': 'form-control'}))

    socket_name = forms.CharField(max_length=25, initial="BEERSOCKET", required=False,
                                  help_text="Name of the file-based socket (Only used if useInetSocket is False)",
                                  widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'BEERSOCKET'}))

    wifi_host = forms.CharField(max_length=40, initial='', required=False,
                                help_text="mDNS host name or IP address for WiFi connected hardware (only used if " +
                                          "connection_type is wifi)",
                                widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: brewpi.local'}))

    wifi_port = forms.IntegerField(initial=23, min_value=10, max_value=65536, required=False,
                                   help_text="The internet port to use (almost always 23)",
                                   widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 1222'}))

    prefer_connecting_via_udev = forms.BooleanField(initial=True, required=False,
                                                    help_text="Whether to autodetect the appropriate serial port " +
                                                              "using the device's USB serial number")

    def clean(self):
        cleaned_data = self.cleaned_data

        # Check the connection type and default parameters that don't apply
        if cleaned_data['connection_type'] == 'serial':
            cleaned_data['wifi_host'] = "NA"
            cleaned_data['wifi_port'] = 23

            # Since we've skipped automated validation above, validate here.
            if cleaned_data['serial_port'] is None or cleaned_data['serial_alt_port'] is None:
                raise forms.ValidationError("Serial Port & Serial Alt Port are required for connection type 'serial'")
            elif len(cleaned_data['serial_port']) < 2:
                raise forms.ValidationError("Must specify a valid serial port when using connection type 'serial'")
            elif len(cleaned_data['serial_alt_port']) < 2:
                raise forms.ValidationError("Must specify a valid alt serial port (or None) when using connection " +
                                            "type 'serial'")

        elif cleaned_data['connection_type'] == 'wifi':
            cleaned_data['serial_port'] = 'auto'
            cleaned_data['serial_alt_port'] = 'None'
            cleaned_data['prefer_connecting_via_udev'] = True

            # Since we've skipped automated validation above, validate here.
            if cleaned_data['wifi_host'] is None or cleaned_data['wifi_port'] is None:
                raise forms.ValidationError("WiFi Host & Port are required for connection type 'WiFi'")
            elif cleaned_data['wifi_port'] < 0 or cleaned_data['wifi_port'] > 65536:
                raise forms.ValidationError("WiFi port must be between 1 and 65536 (but is generally 23)")
            elif len(cleaned_data['wifi_host']) < 5:
                raise forms.ValidationError("Must specify a valid hostname or IP address for WiFi Host")
        else:
            raise forms.ValidationError("Invalid connection type specified")

        # Check if we are using inet sockets to connect to brewpi-script and default parameters that don't apply
        if cleaned_data['useInetSocket']:
            cleaned_data['socket_name'] = "BEERSOCKET"
        else:
            cleaned_data['socketPort'] = 2222
            cleaned_data['socketHost'] = "localhost"

        return cleaned_data


class OldCCModelForm(ModelForm):
    class Meta:
        model = OldControlConstants
        fields = OldControlConstants.firmware_field_list

    def __init__(self, *args, **kwargs):
        super(OldCCModelForm, self).__init__(*args, **kwargs)
        for this_field in self.fields:
            self.fields[this_field].widget.attrs['class'] = "form-control"


class SensorForm(ModelForm):
    class Meta:
        model = SensorDevice
        fields = ['device_function', 'invert', 'pin', 'address']

    def __init__(self, *args, **kwargs):
        super(SensorForm, self).__init__(*args, **kwargs)
        for this_field in self.fields:
            self.fields[this_field].widget.attrs['class'] = "form-control"


class SensorFormRevised(forms.Form):
    device_function = forms.ChoiceField(label="Device Function",
                                        widget=forms.Select(attrs={'class': 'form-control select select-primary',
                                                                   'data-toggle': 'select'}),
                                        choices=SensorDevice.DEVICE_FUNCTION_CHOICES, required=False)
    invert = forms.ChoiceField(label="Invert Pin",
                               widget=forms.Select(attrs={'class': 'form-control select select-primary', 'data-toggle': 'select'}),
                               choices=SensorDevice.INVERT_CHOICES, required=False)
    # Not sure if I want to change 'invert' to be a switch or a dropdown
    # invert = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'data-toggle': 'switch'}))

    address = forms.CharField(widget=forms.HiddenInput, required=False)
    pin = forms.CharField(widget=forms.HiddenInput)
    installed = forms.BooleanField(widget=forms.HiddenInput, initial=False, required=False)

    # perform_uninstall is just used so we can combine all the actions into this form
    perform_uninstall = forms.BooleanField(widget=forms.HiddenInput, initial=False, required=False)

    def clean(self):
        cleaned_data = self.cleaned_data

        # TODO - Add checks for device_function/pin to make sure they're in the valid range
        if cleaned_data.get("perform_uninstall"):
            perform_uninstall = cleaned_data.get("perform_uninstall")
        else:
            perform_uninstall = False

        if perform_uninstall:
            device_function = SensorDevice.DEVICE_FUNCTION_NONE
        else:
            device_function = cleaned_data.get("device_function")  # TODO - Add additional checks based on device type

        pin = int(cleaned_data.get("pin"))
        address = cleaned_data.get("address")

        if cleaned_data.get("installed"):
            installed = cleaned_data.get("installed")
        else:
            installed = False

        if len(address) <= 0:
            if cleaned_data.get("invert"):
                invert = cleaned_data.get("invert")
            elif perform_uninstall is True:
                # We don't care if we're uninstalling
                invert = SensorDevice.INVERT_NOT_INVERTED
            else:
                raise forms.ValidationError("Invert must be specified for non-OneWire devices")
        else:
            invert = SensorDevice.INVERT_NOT_INVERTED

        # All the fields that MAY have been omitted have been set - return cleaned_data
        cleaned_data['invert'] = invert
        cleaned_data['device_function'] = int(device_function)
        cleaned_data['installed'] = installed
        cleaned_data['pin'] = pin  # To handle the int conversion

        return cleaned_data


class TempControlForm(forms.Form):
    # TODO - Add validation for temperature_setting to make sure its in range of the device (somehow)
    TEMP_CONTROL_FUNCTIONS = (
        ('off','Off'),
        ('beer_profile', 'Beer Profile'),
        ('fridge_constant', 'Fridge Constant'),
        ('beer_constant', 'Beer Constant'),
    )

    @staticmethod
    def get_profile_choices():
        choices = []
        available_profiles = FermentationProfile.objects.filter(status=FermentationProfile.STATUS_ACTIVE)
        for this_profile in available_profiles:
            if this_profile.is_assignable():
                profile_tuple = (this_profile.id, this_profile.name)
                choices.append(profile_tuple)
        return choices

    # This is actually going to almost always be hidden, but I'm setting it up as a select class here just in case
    # we ever decide to actually render this form
    temp_control = forms.ChoiceField(label="Temperature Control Function",
                                     widget=forms.Select(attrs={'class': 'form-control select select-primary',
                                                                'data-toggle': 'select'}),
                                     choices=TEMP_CONTROL_FUNCTIONS, required=True)

    temperature_setting = forms.DecimalField(label="Temperature Setting", max_digits=4, decimal_places=1,
                                             required=False)
    profile = forms.ChoiceField(required=False)  # Choices set in __init__ below
    start_at = forms.CharField(help_text="How far into the profile you want to start (optional) " +
                                    "(Example: 7d 3h 15m 4s)",
                          widget=forms.TextInput(attrs={'placeholder': '0h 0s'}), required=False,
                          validators=[validators.RegexValidator(regex="([0-9]+[ ]*[ywdhms]{1}[ ]*)+",
                                                                message="Invalid 'Start At' format")])

    def __init__(self, *args, **kwargs):
        super(TempControlForm, self).__init__(*args, **kwargs)
        # for this_field in self.fields:
        #     self.fields[this_field].widget.attrs['class'] = "form-control"
        self.fields['profile'] = forms.ChoiceField(required=False,
                                                   choices=self.get_profile_choices(),
                                                   widget=forms.Select(attrs={'class': 'form-control'}))

    # Check that the Start At format is valid, and if it is, replace it with a datetime delta object
    def clean_start_at(self):
        # TODO - Convert this to instead use FermentationProfilePoint.string_to_ttl
        # tz = pytz.timezone(getattr(settings, 'TIME_ZONE', False))
        if 'start_at' in self.cleaned_data:
            ttl_text = self.cleaned_data['start_at']
        else:
            return None

        if len(ttl_text) <= 1:
            return None

        # Split out the d/h/m/s of the timer
        try:
            timer_pattern = r"(?P<time_amt>[0-9]+)[ ]*(?P<ywdhms>[ywdhms]{1})"
            timer_regex = re.compile(timer_pattern)
            timer_matches = timer_regex.finditer(ttl_text)
        except:
            raise forms.ValidationError("Start At format is invalid")


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

        return time_delta
