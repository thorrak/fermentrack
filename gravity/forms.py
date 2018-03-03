from django.contrib.auth.models import User
from django import forms
from constance import config
#from constance.admin import ConstanceForm
from django.conf import settings
from gravity.models import GravitySensor, GravityLogPoint, GravityLog, TiltConfiguration, IspindelConfiguration
from app.models import BrewPiDevice
from django.forms import ModelForm


###################################################################################################################
# Generic (Manual) Forms
###################################################################################################################


# Manual sensors don't have special configuration.
class ManualForm(ModelForm):
    class Meta:
        model = GravitySensor
        fields = ['name', 'temp_format',]

    def __init__(self, *args, **kwargs):
        super(ManualForm, self).__init__(*args, **kwargs)
        for this_field in self.fields:
            self.fields[this_field].widget.attrs['class'] = "form-control"

# Manual sensors don't have special configuration.
class ManualPointForm(ModelForm):
    class Meta:
        model = GravityLogPoint
        fields = ['gravity', 'temp', 'temp_format', 'temp_is_estimate', 'extra_data']

    def __init__(self, *args, **kwargs):
        super(ManualPointForm, self).__init__(*args, **kwargs)
        for this_field in self.fields:
            self.fields[this_field].widget.attrs['class'] = "form-control"





class GravityLogCreateForm(forms.Form):
    log_name = forms.CharField(max_length=255, min_length=1, required=True, )
    device = forms.ChoiceField(required=True)

    @staticmethod
    def get_device_choices():
        choices = []
        # We specifically do not want to include any devices that are assigned to temperature controllers as these are
        # being controlled by the linked temperature controller
        available_devices = GravitySensor.objects.filter(assigned_brewpi_device=None)
        for this_device in available_devices:
            device_tuple = (this_device.id, this_device.name)
            choices.append(device_tuple)
        return choices

    def __init__(self, *args, **kwargs):
        super(GravityLogCreateForm, self).__init__(*args, **kwargs)
        for this_field in self.fields:
            self.fields[this_field].widget.attrs['class'] = "form-control"
        self.fields['device'] = forms.ChoiceField(required=True, choices=self.get_device_choices(),
                                                  widget=forms.Select(attrs={'class': 'form-control',
                                                                             'data-toggle': 'select'}))

    def clean(self):
        cleaned_data = self.cleaned_data

        if cleaned_data.get("log_name"):
            # Due to the fact that the beer name is used in file paths, we need to validate it to prevent "injection"
            # type attacks
            log_name = cleaned_data.get("log_name")
            if GravityLog.name_is_valid(log_name):
                cleaned_data['log_name'] = log_name
            else:
                raise forms.ValidationError("Log name must only consist of letters, numbers, dashes, spaces, " +
                                            "and underscores")
        else:
            raise forms.ValidationError("Log name must be specified")

        try:
            linked_device = GravitySensor.objects.get(id=cleaned_data.get('device'))
            cleaned_data['device'] = linked_device
        except:
            raise forms.ValidationError("Invalid device ID specified!")

        if linked_device.assigned_brewpi_device is not None:
            raise forms.ValidationError("This device is managed by a temperature controller - To create a log, go to " +
                                        "the controller's dashboard and start a new beer log there")

        return cleaned_data


class SensorAttachForm(forms.Form):

    sensor = forms.ChoiceField(required=True)
    temp_controller = forms.ChoiceField(required=True)

    @staticmethod
    def get_sensor_choices():
        choices = []
        available_sensors = GravitySensor.objects.filter(assigned_brewpi_device=None)
        for this_device in available_sensors:
            device_tuple = (this_device.id, this_device.name)
            choices.append(device_tuple)
        return choices

    @staticmethod
    def get_controller_choices():
        choices = []
        available_devices = BrewPiDevice.objects.filter(gravity_sensor=None)
        for this_device in available_devices:
            device_tuple = (this_device.id, this_device.device_name)
            choices.append(device_tuple)
        return choices


    def __init__(self, *args, **kwargs):
        super(SensorAttachForm, self).__init__(*args, **kwargs)
        for this_field in self.fields:
            self.fields[this_field].widget.attrs['class'] = "form-control"
        self.fields['sensor'] = forms.ChoiceField(required=True, choices=self.get_sensor_choices(),
                                                  widget=forms.Select(attrs={'class': 'form-control',
                                                                             'data-toggle': 'select'}))
        self.fields['temp_controller'] = forms.ChoiceField(required=True, choices=self.get_controller_choices(),
                                                           widget=forms.Select(attrs={'class': 'form-control',
                                                                                      'data-toggle': 'select'}))

    def clean(self):
        cleaned_data = self.cleaned_data

        try:
            sensor = GravitySensor.objects.get(id=cleaned_data.get('sensor'), assigned_brewpi_device=None)
            cleaned_data['sensor'] = sensor
        except:
            raise forms.ValidationError("Invalid gravity sensor specified!")

        try:
            temp_controller = BrewPiDevice.objects.get(id=cleaned_data.get('temp_controller'), gravity_sensor=None)
            cleaned_data['temp_controller'] = temp_controller
        except:
            raise forms.ValidationError("Invalid temperature controller specified!")

        return cleaned_data



class TiltCreateForm(forms.Form):
    name = forms.CharField(max_length=255, min_length=1, required=True, )
    temp_format = forms.ChoiceField(required=True, choices=GravitySensor.TEMP_FORMAT_CHOICES)

    color = forms.ChoiceField(required=True, choices=TiltConfiguration.COLOR_CHOICES)

    def clean_color(self):
        if self.cleaned_data.get("color"):
            # Although the color uniqueness check is enforced on the database insert, I want to check it here as well
            try:
                # If an object already exists with the color that was specified, error out.
                obj_with_color = TiltConfiguration.objects.get(color=self.cleaned_data['color'])
            except:
                obj_with_color = None

            if obj_with_color is not None:
                raise forms.ValidationError("There is already a Tilt sensor configured with "
                                            "the color {}".format(self.cleaned_data['color']))
        else:
            raise forms.ValidationError("Tilt sensors require a color to be specified")

        return self.cleaned_data['color']

    def __init__(self, *args, **kwargs):
        super(TiltCreateForm, self).__init__(*args, **kwargs)
        for this_field in self.fields:
            self.fields[this_field].widget.attrs['class'] = "form-control"


class IspindelCreateForm(forms.Form):
    name = forms.CharField(max_length=255, min_length=1, required=True, )
    temp_format = forms.ChoiceField(required=True, choices=GravitySensor.TEMP_FORMAT_CHOICES)
    name_on_device = forms.CharField(max_length=64, min_length=1, required=True,
                                     widget=forms.TextInput(attrs={'placeholder': 'iSpindel000'}))

    # Allow for inputting the coefficients/constant term of the gravity equation (if known)
    a = forms.DecimalField(required=False, help_text="The third degree coefficient of the gravity equation")
    b = forms.DecimalField(required=False, help_text="The second degree coefficient of the gravity equation")
    c = forms.DecimalField(required=False, help_text="The first degree coefficient of the gravity equation")
    d = forms.DecimalField(required=False, help_text="The constant term of the gravity equation")

    def clean_name_on_device(self):
        if self.cleaned_data.get("name_on_device"):
            # Although the name_on_device uniqueness check is enforced on the database insert, I want to check it here as well
            try:
                # If an object already exists with the name_on_device that was specified, error out.
                obj_with_name = IspindelConfiguration.objects.get(name_on_device=self.cleaned_data['name_on_device'])
            except:
                obj_with_name = None

            if obj_with_name is not None:
                raise forms.ValidationError("There is already an iSpindel sensor configured with "
                                            "the name {}".format(self.cleaned_data['name_on_device']))
        else:
            raise forms.ValidationError("iSpindel sensors require a name on device to be specified")

        return self.cleaned_data['name_on_device']

    def __init__(self, *args, **kwargs):
        super(IspindelCreateForm, self).__init__(*args, **kwargs)
        for this_field in self.fields:
            self.fields[this_field].widget.attrs['class'] = "form-control"

