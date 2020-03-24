from django import forms

from .models import BreweryLogo
from django.core import validators
import fermentrack_django.settings as settings

from django.forms import ModelForm


class BreweryLogoForm(forms.ModelForm):

    class Meta:
        model = BreweryLogo
        fields = ['name', 'image', 'externalURL']
        help_texts = ['image': "The file name of your image must be brewerylogo.png"]
