from django import forms
from app.models import BrewPiDevice, OldControlConstants, NewControlConstants, SensorDevice, FermentationProfile, FermentationProfilePoint
from django.core import validators
import fermentrack_django.settings as settings
from django.core.exceptions import ObjectDoesNotExist

from django.forms import ModelForm
from . import udev_integration

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

    # modify_not_create is a flag that impacts the device name checking in clean_device_name()
    modify_not_create = forms.BooleanField(widget=forms.HiddenInput, initial=False, required=False)

    def clean_device_name(self):
        if 'device_name' not in self.cleaned_data:
            raise forms.ValidationError("A device name must be specified")
        else:
            device_name = self.cleaned_data['device_name']

        # Name uniqueness is enforced on the sql CREATE, but since we're not using a ModelForm this form won't check to
        # see if the name is actually uniqye. That said - we only need to check if we're creating the object. We do not
        # need to check if we're modifying the object.
        if 'modify_not_create' not in self.cleaned_data:
            modify_not_create = False
        else:
            modify_not_create = self.cleaned_data['modify_not_create']

        if not modify_not_create:  # If we're creating, not modifying
            try:
                existing_device = BrewPiDevice.objects.get(device_name=device_name)
                raise forms.ValidationError("A device already exists with the name {}".format(device_name))

            except ObjectDoesNotExist:
                # There was no existing device - we're good.
                return device_name
        else:
            # For modifications, we always return the device name
            return device_name

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

            if 'prefer_connecting_via_udev' in cleaned_data and cleaned_data['prefer_connecting_via_udev']:
                # The user clicked "prefer_connecting_via_udev". Check if there is another device that already exists
                # with the same udev serial number, and if there is, raise an error.
                udev = udev_integration.get_serial_from_node(cleaned_data['serial_port'])
                devices_with_udev = BrewPiDevice.objects.filter(udev_serial_number=udev)

                if len(devices_with_udev) != 0:
                    raise forms.ValidationError("Prefer connecting via udev is set, but another device "
                                                "is set up with a similar udev serial number. To proceed, uncheck "
                                                "this option or remove the other device.")
            else:
                # The user didn't click "prefer_connecting_via_udev". Check two things:
                # First, check that there isn't a device that exists already with the same serial_port or serial_alt_port

                devices_with_port = BrewPiDevice.objects.filter(serial_port=cleaned_data['serial_port'])
                devices_with_port_alt = BrewPiDevice.objects.filter(serial_alt_port=cleaned_data['serial_port'])
                devices_with_alt = BrewPiDevice.objects.filter(serial_port=cleaned_data['serial_alt_port'])
                devices_with_alt_alt = BrewPiDevice.objects.filter(serial_alt_port=cleaned_data['serial_alt_port'])

                if len(devices_with_port) != 0 or len(devices_with_port_alt) != 0 or len(devices_with_alt) != 0 or len(devices_with_alt_alt) != 0:
                    raise forms.ValidationError("A device is already set up with that serial port or alternate serial "
                                                "port. To proceed, change ports, or remove the other device.")

                udev = udev_integration.get_serial_from_node(cleaned_data['serial_port'])
                devices_with_udev = BrewPiDevice.objects.filter(udev_serial_number=udev)

                for this_device in devices_with_udev:
                    if this_device.prefer_connecting_via_udev:
                        raise forms.ValidationError("The device {} has a ".format(this_device) +
                                                    "conflicting udev serial number to the one you are currently"
                                                    "attempting to set up, and has 'prefer connecting via udev' turned"
                                                    "on. This can cause unexpected behavior. Please disable this option"
                                                    "on the other device (or delete it entirely) to proceed with adding"
                                                    "this one.")

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


class NewCCModelForm(ModelForm):
    class Meta:
        model = NewControlConstants
        fields = NewControlConstants.firmware_field_list

    def __init__(self, *args, **kwargs):
        super(NewCCModelForm, self).__init__(*args, **kwargs)
        for this_field in self.fields:
            self.fields[this_field].widget.attrs['class'] = "form-control"


class SensorForm(ModelForm):
    # TODO - Delete if no longer required
    class Meta:
        model = SensorDevice
        fields = ['device_function', 'invert', 'pin', 'address']

    def __init__(self, *args, **kwargs):
        super(SensorForm, self).__init__(*args, **kwargs)
        for this_field in self.fields:
            self.fields[this_field].widget.attrs['class'] = "form-control"


class SensorFormRevised(forms.Form):
    # TODO - Overwrite the DEVICE_FUNCTION_CHOICES to match the type of device being configured
    device_function = forms.ChoiceField(label="Device Function",
                                        widget=forms.Select(attrs={'class': 'form-control select select-primary',
                                                                   'data-toggle': 'select'}),
                                        choices=SensorDevice.DEVICE_FUNCTION_CHOICES, required=False)
    invert = forms.ChoiceField(label="Invert Pin",
                               widget=forms.Select(attrs={'class': 'form-control select select-primary', 'data-toggle': 'select'}),
                               choices=SensorDevice.INVERT_CHOICES, required=False)
    # Not sure if I want to change 'invert' to be a switch or a dropdown
    # invert = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'data-toggle': 'switch'}))

    calibration = forms.FloatField(label="Temp Calibration Offset", required=False, initial=0.0,
                                   help_text="The temperature calibration to be added to each reading (in case "
                                             "your temperature sensors misread temps)")

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
        cleaned_data['perform_uninstall'] = perform_uninstall

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
        if 'start_at' in self.cleaned_data:
            ttl_text = self.cleaned_data['start_at']
        else:
            return None

        if len(ttl_text) <= 1:
            return None

        return FermentationProfilePoint.string_to_ttl(ttl_text)

    def clean(self):
        cleaned_data = self.cleaned_data

        if 'temp_control' in cleaned_data:
            if cleaned_data['temp_control'] == 'off':
                # If temp control is off, we don't need a profile or setting
                return cleaned_data
            elif cleaned_data['temp_control'] == 'beer_constant' or cleaned_data['temp_control'] == 'fridge_constant':
                # For constant modes, we must have a temperature setting
                if 'temperature_setting' in cleaned_data:
                    if cleaned_data['temperature_setting'] is None:
                        raise forms.ValidationError("A temperature setting must be provided for 'constant' modes")
                    else:
                        return cleaned_data
                else:
                    raise forms.ValidationError("A temperature setting must be provided for 'constant' modes")
            elif cleaned_data['temp_control'] == 'beer_profile':
                # and for profile modes, we must have a profile
                if 'profile' in cleaned_data:
                    return cleaned_data
                else:
                    raise forms.ValidationError("A temperature profile must be provided for 'profile' modes")
            else:
                raise forms.ValidationError("Invalid temperature control mode specified!")
        else:
            raise forms.ValidationError("Temperature control mode must be specified!")

