from django import forms
from app.models import BrewPiDevice, InstallSettings, OldControlConstants, NewControlConstants, SensorDevice
from django.core import validators
import brewpi_django.settings as settings

from django.forms import ModelForm

import re
import datetime
import pytz




class DeviceForm(forms.Form):

    device_name = forms.CharField(max_length=48, help_text="Unique name for this device",
                                  widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Device Name'}))
    temp_format = forms.ChoiceField(choices=BrewPiDevice.TEMP_FORMAT_CHOICES, initial='C', help_text="Temperature units",
                                    widget=forms.Select(attrs={'class': 'form-control'}))
    data_point_log_interval = forms.ChoiceField(initial=10, choices=BrewPiDevice.DATA_POINT_TIME_CHOICES,
                                                help_text="Time between logged data points",
                                                widget=forms.Select(attrs={'class': 'form-control'}))
    connection_type = forms.ChoiceField(initial='serial', choices=BrewPiDevice.CONNECTION_TYPE_CHOICES,
                                        help_text="Type of connection between the Raspberry Pi and the hardware",
                                        widget=forms.Select(attrs={'class': 'form-control'}))
    has_old_brewpi_www = forms.BooleanField(required=False, help_text="Does this device also have the old-style (PHP-based) brewpi-www installed somewhere?")
    wwwPath = forms.CharField(max_length=255, help_text="Path to the BrewPi-www installation (deprecated??)", initial="/var/www", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '/var/www'}))
    useInetSocket = forms.BooleanField(required=False, help_text="Whether or not to use an internet socket (rather than local)", initial=True)
    socketPort = forms.IntegerField(initial=2222, min_value=10, max_value=65536, help_text="The internet socket to use (only used if useInetSocket above is \"True\")", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 1234'}))

    socketHost = forms.CharField(max_length=128, initial="localhost", help_text="The interface to bind for the "
                                                                                "internet socket (only used if "
                                                                                "useInetSocket above is \"True\")",
                                 widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: localhost'}))

    # # TODO - Determine if script_path can be eliminated given we are using a custom brewpi-script
    # script_path = forms.CharField(max_length=255, help_text="Path to the BrewPi script (deprecated??)", initial="/home/brewpi/",
    #                               widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '/home/brewpi/'}))
    serial_port = forms.CharField(max_length=255, help_text="Serial port to which the BrewPi device is connected (Only used if connection_type is serial)", initial="auto", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'auto'}))
    serial_alt_port = forms.CharField(max_length=255, help_text="Alternate serial port path (Only used if connection_type is serial)", initial="None", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'None'}))

    board_type = forms.ChoiceField(initial="uno", choices=BrewPiDevice.BOARD_TYPE_CHOICES, help_text="Board type to which BrewPi is connected", widget=forms.Select(attrs={'class': 'form-control'}))

    socket_name = forms.CharField(max_length=25, initial="BEERSOCKET", help_text="Name of the file-based socket (Only" +
                                                                                 " used if useInetSocket is False)",
                                  widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'BEERSOCKET'}))

    wifi_host = forms.CharField(max_length=40, initial='',
                                help_text="mDNS host name or IP address for WiFi connected hardware (only used if " +
                                          "connection_type is wifi)",
                                widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: brewpi.local'}))
    wifi_port = forms.IntegerField(initial=23, min_value=10, max_value=65536,
                                    help_text="The internet port to use (almost always 23)",
                                   widget=forms.TextInput(
                                       attrs={'class': 'form-control', 'placeholder': 'Ex: 1222'}))



class ScriptSettingsForm(forms.Form):

    date_time_format_display = forms.ChoiceField(initial="mm/dd/yy", choices=InstallSettings.DATE_TIME_FORMAT_DISPLAY_CHOICES)



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
    device_function = forms.ChoiceField(label="Device Function", widget=forms.Select, choices=SensorDevice.DEVICE_FUNCTION_CHOICES, required=False)
    invert = forms.ChoiceField(label="Invert Pin", widget=forms.Select, choices=SensorDevice.INVERT_CHOICES, required=False)

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

        pin = cleaned_data.get("pin")
        address = cleaned_data.get("address")

        if cleaned_data.get("installed"):
            installed = cleaned_data.get("installed")
        else:
            installed = False

        if address is None:
            if cleaned_data.get("invert"):
                invert = cleaned_data.get("invert")
            else:
                raise forms.ValidationError("Invert must be specified for non-OneWire devices")
        else:
            invert = SensorDevice.INVERT_NOT_INVERTED

        # All the fields that MAY have been omitted have been set - return cleaned_data
        cleaned_data['invert'] = invert
        cleaned_data['device_function'] = int(device_function)
        cleaned_data['installed'] = installed

        return cleaned_data

