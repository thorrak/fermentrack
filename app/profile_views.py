from django.shortcuts import render
from django.contrib import messages
from django.shortcuts import render_to_response, redirect

import device_forms
import profile_forms


import json, time

from app.models import BrewPiDevice, FermentationProfilePoint, FermentationProfile

# Cheating on this one.
from views import render_with_devices


def profile_new(request):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.add_fermentation_profile'):
    #     messages.error(request, 'Your account is not permissioned to add fermentation profiles. Please contact an admin')
    #     return redirect("/")

    if request.POST:
        form = profile_forms.FermentationProfileForm(request.POST)
        if form.is_valid():
            # Generate the new_control_constants object from the form data
            new_fermentation_profile = form.save()
            messages.success(request, 'New fermentation profile \'{}\' created'.format(new_fermentation_profile.name))
            return redirect("/")  # TODO - Change this to redirect to the fermentation profile view screen

        else:
            return render_with_devices(request, template_name='profile/profile_new.html', context={'form': form})
    else:
        form = profile_forms.FermentationProfileForm()
        return render_with_devices(request, template_name='profile/profile_new.html', context={'form': form})


# TODO - Determine if profile_edit & profile_view should be combined (possibly when implementing inline edits??)
def profile_edit(request, profile_id):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.edit_fermentation_profile'):
    #     messages.error(request, 'Your account is not permissioned to edit fermentation profiles. Please contact an admin')
    #     return redirect("/")

    if request.POST:
        form = profile_forms.FermentationProfileForm(request.POST)
        if form.is_valid():
            # Generate the new_control_constants object from the form data
            new_fermentation_profile = form.save()
            messages.success(request, 'New fermentation profile \'{}\' created'.format(new_fermentation_profile.name))
            return redirect("/")  # TODO - Change this to redirect to the fermentation profile view screen

        else:
            return render_with_devices(request, template_name='profile/profile_edit.html', context={'form': form})
    else:
        form = profile_forms.FermentationProfileForm()
        return render_with_devices(request, template_name='profile/profile_edit.html', context={'form': form})


def profile_list(request):
    all_profiles = FermentationProfile.objects.all()
    return render_with_devices(request, template_name='profile/profile_list.html', context={'all_profiles': all_profiles})
