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




    # system_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'typeahead-regions',
    #                                                             'data-provide': 'typeahead', 'autocomplete': 'off'}))
    # planet_number = forms.CharField(min_length=1)
    # moon_number = forms.CharField(min_length=0)

    # timer = forms.CharField(help_text="1d 2h 3m 4s", validators=[validators.RegexValidator(regex="([0-9]+[ ]*[dhms]{1}[ ]*)+",message="Invalid timer format")])
    # notes = forms.CharField(min_length=0, widget=forms.Textarea, required=False)


    # Validate the system name is valid
    # def clean_system_name(self):
    #     system_name = self.cleaned_data['system_name']
    #
    #     try:
    #         this_system = eveSystem.objects.get(name__iexact=system_name)
    #         return this_system.id
    #         # else:
    #         #     raise forms.ValidationError("System '" + system_name + "'doesn't exist.")
    #     except:
    #         if self.cleaned_data['system_name']:
    #             raise forms.ValidationError("System '{0}' doesn't exist".format(system_name))
    #         else:
    #             raise forms.ValidationError("System provided doesn't exist")
    #
    #
    # # Check that the timer format is valid, and if it is, replace it with a datetime object
    # def clean_timer(self):
    #     tz = pytz.timezone(getattr(settings, 'TIME_ZONE', False))
    #     new_timer = self.cleaned_data['timer']
    #
    #     # Split out the d/h/m/s of the timer
    #     try:
    #         timer_pattern = r"(?P<time_amt>[0-9]+)[ ]*(?P<dhms>[dhms]{1})"
    #         timer_regex = re.compile(timer_pattern)
    #         timer_matches = timer_regex.finditer(new_timer)
    #     except:
    #         raise forms.ValidationError("Timer format is invalid")
    #
    #
    #     # timer_time is equal to now + the time delta
    #     timer_time = tz.localize(datetime.datetime.now())
    #     for this_match in timer_matches:
    #         dhms = this_match.group('dhms')
    #         delta_amt = int(this_match.group('time_amt'))
    #         if dhms == 'd':
    #             timer_time = timer_time + datetime.timedelta(days=delta_amt)
    #         elif dhms == 'h':
    #             timer_time = timer_time + datetime.timedelta(hours=delta_amt)
    #         elif dhms == 'm':
    #             timer_time = timer_time + datetime.timedelta(minutes=delta_amt)
    #         elif dhms == 's':
    #             timer_time = timer_time + datetime.timedelta(seconds=delta_amt)
    #
    #     # return self.cleaned_data['timer']
    #     return timer_time
    #
    #
    # def clean(self):
    #     cleaned_data = self.cleaned_data
    #
    #     system_name = cleaned_data.get("system_name")
    #     planet_num = cleaned_data.get("planet_number")
    #     moon_num = cleaned_data.get("moon_number")
    #     structure_type = cleaned_data.get("structure_type")
    #
    #     # First, determine the celestial type based on the structure
    #     if structure_type:
    #         if structure_type == "TOW":
    #             # Only towers go on moons
    #             cleaned_data['celestial_type'] = "MN"
    #
    #             # Additionally, while we're here, make sure for towers we have a size selected
    #             tower_size = cleaned_data.get("tower_size")
    #             if tower_size:
    #                 if tower_size == "NA":
    #                     raise forms.ValidationError("Must specify tower size for tower timers")
    #
    #
    #         elif structure_type != "SBU" and structure_type != "UNK":
    #             # All other structures except SBUs go on planets
    #             cleaned_data['celestial_type'] = "PL"
    #             cleaned_data['moon_number'] = "0"   # For planet-based structures, reset the moon to 0
    #             cleaned_data['tower_size'] = "NA"
    #         else:
    #             cleaned_data['celestial_type'] = "NA"
    #             cleaned_data['tower_size'] = "NA"
    #
    #
    #     # Next, test if we can look up a system based on the system name
    #     if system_name:
    #         system = eveSystem.objects.get(id=system_name)  # In clean_system_name above name gets swapped for id
    #     else:
    #         raise forms.ValidationError("Unable to locate system")
    #
    #
    #     celestial_type = cleaned_data.get("celestial_type")
    #
    #     if celestial_type and system:
    #         if celestial_type == "MN":
    #             # If we have a moon, check that we have a planet and moon number
    #             if planet_num and moon_num:
    #                 if planet_num > 0 and moon_num > 0:
    #                     # Ok, we can start validating. Start by pulling the planet
    #                     try:
    #                         planet = evePlanet.objects.get(system_id=system.id, celestial_index=planet_num)
    #                     except:
    #                         raise forms.ValidationError("Planet specified is invalid for this system")
    #
    #                     if planet: # If we succeeded in pulling the planet, awesome. Pull the moon next.
    #                         try:
    #                             moon = eveMoon.objects.get(planet_id=planet.id, celestial_index=moon_num)
    #                             cleaned_data['celestial'] = moon.id  # We found the moon, set the celestial ID
    #                         except:
    #                             raise forms.ValidationError("Planet specified is invalid for this system")
    #                 else:
    #                     # Either planet or moon num wasn't greater than 0
    #                     raise forms.ValidationError("For moon-based structures, planet & moon number must be greater than 0")
    #             else:
    #                 # Either planet or moon num wasn't valid
    #                 raise forms.ValidationError("For moon-based structures, planet & moon number must be present and greater than 0")
    #
    #
    #         elif celestial_type == "PL":
    #             # If we have a planet, check that we have a planet number
    #             if planet_num:
    #                 if planet_num > 0:
    #                     # Ok, we can start validating. Start by pulling the planet
    #                     try:
    #                         planet = evePlanet.objects.get(system_id=system.id, celestial_index=planet_num)
    #                         cleaned_data['celestial'] = planet.id  # We found the planet, set the celestial ID
    #                     except:
    #                         raise forms.ValidationError("Planet specified is invalid for this system")
    #                 else:
    #                     # Planet number is 0 or less
    #                     raise forms.ValidationError("For planet-based structures, planet number must be greater than 0")
    #             else:
    #                 # Planet number wasn't valid
    #                 raise forms.ValidationError("For planet-based structures, planet number must be present and greater than 0")
    #
    #         else:
    #             cleaned_data['celestial'] = "0"  # Set to 0 by default
    #
    #
    #     # Ideally, at this point, both celestial and celestial_type have been set if the form data was valid.
    #     # Return cleaned data back to the handler
    #     return cleaned_data




class ScriptSettingsForm(forms.Form):

    date_time_format_display = forms.ChoiceField(initial="mm/dd/yy", choices=InstallSettings.DATE_TIME_FORMAT_DISPLAY_CHOICES)


class OldControlConstantsForm(forms.Form):
    tempSetMin = forms.FloatField(max_value=None, min_value=None)
    tempSetMax = forms.FloatField(max_value=None, min_value=None)

    Kp = forms.FloatField(max_value=None, min_value=None)
    Ki = forms.FloatField(max_value=None, min_value=None)
    Kd = forms.FloatField(max_value=None, min_value=None)

    pidMax = forms.FloatField(max_value=None, min_value=None)
    iMaxErr = forms.FloatField(max_value=None, min_value=None)

    idleRangeH = forms.FloatField(max_value=None, min_value=None)
    idleRangeL = forms.FloatField(max_value=None, min_value=None)

    heatTargetH = forms.FloatField(max_value=None, min_value=None)
    heatTargetL = forms.FloatField(max_value=None, min_value=None)

    coolTargetH = forms.FloatField(max_value=None, min_value=None)
    coolTargetL = forms.FloatField(max_value=None, min_value=None)

    maxHeatTimeForEst = forms.FloatField(max_value=None, min_value=None)
    maxCoolTimeForEst = forms.FloatField(max_value=None, min_value=None)

    beerFastFilt = forms.FloatField(max_value=None, min_value=None)
    beerSlowFilt = forms.FloatField(max_value=None, min_value=None)
    beerSlopeFilt = forms.FloatField(max_value=None, min_value=None)

    fridgeFastFilt = forms.FloatField(max_value=None, min_value=None)
    fridgeSlowFilt = forms.FloatField(max_value=None, min_value=None)
    fridgeSlopeFilt = forms.FloatField(max_value=None, min_value=None)

    lah = forms.FloatField(max_value=None, min_value=None)
    hs = forms.FloatField(max_value=None, min_value=None)



    data_point_log_interval = forms.ChoiceField(initial=10, choices=BrewPiDevice.DATA_POINT_TIME_CHOICES,
                                                  help_text="Time between logged data points")
    connection_type = forms.ChoiceField(initial='serial', choices=BrewPiDevice.CONNECTION_TYPE_CHOICES,
                                       help_text="Type of connection between the Raspberry Pi and the hardware")
    has_old_brewpi_www = forms.BooleanField(required=False, help_text="Does this device also have the old-style (PHP-based) brewpi-www installed somewhere?")
    wwwPath = forms.CharField(max_length=255, help_text="Path to the BrewPi-www installation (deprecated??)", initial="/var/www")
    useInetSocket = forms.BooleanField(required=False, help_text="Whether or not to use an internet socket (rather than local)")
    socketPort = forms.IntegerField(initial=2222, min_value=10, max_value=65536, help_text="The internet socket to use (only used if useInetSocket above is \"True\")")

    board_type = forms.ChoiceField(initial="uno", choices=BrewPiDevice.BOARD_TYPE_CHOICES, help_text="Board type to which BrewPi is connected")

    socket_name = forms.CharField(max_length=25, initial="BEERSOCKET", help_text="Name of the file-based socket (Only" +
                                                                                 " used if useInetSocket is False)")

    wifi_host = forms.CharField(max_length=40, initial='None',
                                 help_text="mDNS host name or IP address for WiFi connected hardware (only used if " +
                                           "connection_type is wifi)")
    wifi_port = forms.IntegerField(initial=23, min_value=10, max_value=65536,
                                    help_text="The internet socket to use (only used if connection_type is wifi)")

class OldCCModelForm(ModelForm):
    class Meta:
        model = OldControlConstants
        fields = OldControlConstants.firmware_field_list
        # fields = ['tempSetMin', 'tempSetMax', 'Kp', 'Ki', 'Kd', 'pidMax', 'iMaxErr', 'idleRangeH', 'idleRangeL',
        #           'heatTargetH', 'heatTargetL', 'coolTargetH', 'coolTargetL', 'maxHeatTimeForEst', 'maxCoolTimeForEst',
        #           'beerFastFilt', 'beerSlowFilt', 'beerSlopeFilt', 'fridgeFastFilt', 'fridgeSlowFilt',
        #           'fridgeSlopeFilt', 'lah', 'hs',]


    def __init__(self, *args, **kwargs):
        super(OldCCModelForm, self).__init__(*args, **kwargs)
        for this_field in self.fields:
            self.fields[this_field].widget.attrs['class'] = "form-control"
        # self.fields['specie'].queryset = Specie.objects.all(attrs={'class': 'autocomplete'})


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


class FermentationProfileForm(ModelForm):
    class Meta:
        model = OldControlConstants
        fields = OldControlConstants.firmware_field_list
        # fields = ['tempSetMin', 'tempSetMax', 'Kp', 'Ki', 'Kd', 'pidMax', 'iMaxErr', 'idleRangeH', 'idleRangeL',
        #           'heatTargetH', 'heatTargetL', 'coolTargetH', 'coolTargetL', 'maxHeatTimeForEst', 'maxCoolTimeForEst',
        #           'beerFastFilt', 'beerSlowFilt', 'beerSlopeFilt', 'fridgeFastFilt', 'fridgeSlowFilt',
        #           'fridgeSlopeFilt', 'lah', 'hs',]


    def __init__(self, *args, **kwargs):
        super(FermentationProfileForm, self).__init__(*args, **kwargs)
        for this_field in self.fields:
            self.fields[this_field].widget.attrs['class'] = "form-control"


