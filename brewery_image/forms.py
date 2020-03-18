from django import forms

from .models import Image
from django.core import validators
import fermentrack_django.settings as settings

from django.forms import ModelForm


class ImageForm(forms.ModelForm):

    class Meta:
        model = Image
        fields = ['name', 'image', 'externalURL']
