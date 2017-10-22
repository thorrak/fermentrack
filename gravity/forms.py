from django.contrib.auth.models import User
from django import forms
from constance import config
#from constance.admin import ConstanceForm
from django.conf import settings
from gravity.models import GravitySensor, GravityLogPoint, GravityLog
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




class BoardForm(forms.Form):
    DEVICE_BOARD_CHOICES = (
    )

    board_type = forms.ChoiceField(label="Board Type",
                                   widget=forms.Select(attrs={'class': 'form-control', 'data-toggle': 'select'}),
                                   choices=DEVICE_BOARD_CHOICES, required=True)

    def set_choices(self, family):
        # There's probably a better way of doing this
        board_choices = [(brd.id, brd.name) for brd in Board.objects.filter(family=family)]

        self.fields['board_type'].choices = board_choices


# class GuidedDeviceFlashForm(forms.Form):
#     DEVICE_FAMILY_CHOICES = GuidedDeviceSelectForm.DEVICE_FAMILY_CHOICES
#
#     device_family = forms.ChoiceField(label="Device Family",
#                                       widget=forms.Select(attrs={'class': 'form-control',
#                                                                  'data-toggle': 'select'}),
#                                       choices=DEVICE_FAMILY_CHOICES, required=True)
#     should_flash_device = forms.BooleanField(widget=forms.HiddenInput, required=False, initial=False)
#
#
