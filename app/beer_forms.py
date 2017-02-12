from django import forms
from app.models import Beer, BrewPiDevice
from django.core import validators


class BeerCreateForm(forms.Form):
    beer_name = forms.CharField(max_length=255, min_length=1, required=True, )
    device = forms.ChoiceField(required=True)

    @staticmethod
    def get_device_choices():
        choices = []
        available_devices = BrewPiDevice.objects.all()
        for this_device in available_devices:
            device_tuple = (this_device.id, this_device.device_name)
            choices.append(device_tuple)
        return choices

    def __init__(self, *args, **kwargs):
        super(BeerCreateForm, self).__init__(*args, **kwargs)
        for this_field in self.fields:
            self.fields[this_field].widget.attrs['class'] = "form-control"
        self.fields['device'] = forms.ChoiceField(required=True, choices=self.get_device_choices(),
                                                  widget=forms.Select(attrs={'class': 'form-control',
                                                                             'data-toggle': 'select'}))

    def clean(self):
        cleaned_data = self.cleaned_data

        if cleaned_data.get("beer_name"):
            # Due to the fact that the beer name is used in file paths, we need to validate it to prevent "injection"
            # type attacks
            beer_name = cleaned_data.get("beer_name")
            if Beer.name_is_valid(beer_name):
                cleaned_data['beer_name'] = beer_name
            else:
                raise forms.ValidationError("Beer name must only consist of letters, numbers, dashes, spaces, and underscores")
        else:
            raise forms.ValidationError("Beer name must be specified")

        try:
            linked_device = BrewPiDevice.objects.get(id=cleaned_data.get('device'))
            cleaned_data['device'] = linked_device
        except:
            raise forms.ValidationError("Invalid device ID specified!")

        return cleaned_data



