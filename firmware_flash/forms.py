from django.contrib.auth.models import User
from django import forms
from constance import config
#from constance.admin import ConstanceForm
from django.conf import settings
from models import DeviceFamily, Firmware


###################################################################################################################
# Firmware Flash Forms
###################################################################################################################


class FirmwareFamilyForm(forms.Form):
    DEVICE_FAMILY_CHOICES = (
    )

    device_family = forms.ChoiceField(label="Device Family",
                                      widget=forms.Select(attrs={'class': 'form-control',
                                                                 'data-toggle': 'select'}),
                                      choices=DEVICE_FAMILY_CHOICES, required=True)


    def __init__(self, *args, **kwargs):
        super(FirmwareFamilyForm, self).__init__(*args, **kwargs)
        for this_field in self.fields:
            self.fields[this_field].widget.attrs['class'] = "form-control"

        family_choices = [(fam.id, fam.name) for fam in DeviceFamily.objects.all()]

        self.fields['device_family'].choices = family_choices


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
