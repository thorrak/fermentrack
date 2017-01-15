from django.shortcuts import render
from django.contrib import messages
from django.shortcuts import render_to_response, redirect

import device_forms
import profile_forms

from constance import config


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
            # Generate the new_fermentation_profile object from the form data
            new_fermentation_profile = form.save()
            messages.success(request, 'New fermentation profile \'{}\' created'.format(new_fermentation_profile.name))
            return redirect('profile_edit', profile_id=new_fermentation_profile.id)

        else:
            return render_with_devices(request, template_name='profile/profile_new.html', context={'form': form})
    else:
        form = profile_forms.FermentationProfileForm()
        return render_with_devices(request, template_name='profile/profile_new.html', context={'form': form})


# TODO - Determine if profile_edit & profile_view should be combined (and possibly implement inline edits??)
def profile_edit(request, profile_id):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.edit_fermentation_profile'):
    #     messages.error(request, 'Your account is not permissioned to edit fermentation profiles. Please contact an admin')
    #     return redirect("/")

    try:
        this_profile = FermentationProfile.objects.get(id=profile_id)
        this_profile_points = this_profile.fermentationprofilepoint_set.order_by('ttl')
    except:
        # The URL contained an invalid profile ID. Redirect to the profile list.
        messages.error(request, 'Invalid profile \'{}\' selected for editing'.format(profile_id))
        return redirect('profile_list')

    if request.POST:
        form = profile_forms.FermentationProfilePointForm(request.POST)
        if form.is_valid():
            new_profile_point = FermentationProfilePoint(
                profile=this_profile,
                ttl=form.cleaned_data['ttl'],
                temperature_setting=form.cleaned_data['temperature_setting'],
                temp_format=config.TEMPERATURE_FORMAT,  # Arguably, I could add this to the form
            )
            new_profile_point.save()
            this_profile_points = FermentationProfilePoint.objects.filter(profile=this_profile).order_by('ttl')

            # Regardless of whether we were successful or not - rerender the existing edit page

        return render_with_devices(request, template_name='profile/profile_edit.html',
                                       context={'form': form, 'this_profile': this_profile,
                                                'this_profile_points': this_profile_points})
    else:
        form = profile_forms.FermentationProfilePointForm()
        return render_with_devices(request, template_name='profile/profile_edit.html',
                                   context={'form': form, 'this_profile': this_profile,
                                            'this_profile_points': this_profile_points})


def profile_list(request):
    # There must be a better way to implement cleaning up profiles pending deletion...
    FermentationProfile.cleanup_pending_delete()

    all_profiles = FermentationProfile.objects.all()
    return render_with_devices(request, template_name='profile/profile_list.html', context={'all_profiles': all_profiles})


def profile_setpoint_delete(request, profile_id, point_id):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.edit_fermentation_profile'):
    #     messages.error(request, 'Your account is not permissioned to edit fermentation profiles. Please contact an admin')
    #     return redirect("/")

    try:
        this_profile_point = FermentationProfilePoint.objects.get(id=point_id)
    except:
        # The URL contained an invalid profile ID. Redirect to the profile list.
        messages.error(request, 'Invalid profile setpoint selected for deletion')
        return redirect('profile_edit', profile_id=profile_id)

    if not this_profile_point.profile.is_editable():
        # Due to the way we're implementing fermentation profiles, we don't want any edits (including deletion of
        # points!) to a profile that is currently in use.
        messages.error(request, 'Unable to edit a fermentation profile that is currently in use')
    else:
        this_profile_point.delete()
        messages.success(request, 'Setpoint deleted')

    return redirect('profile_edit', profile_id=profile_id)


def profile_delete(request, profile_id):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.edit_fermentation_profile'):
    #     messages.error(request, 'Your account is not permissioned to edit fermentation profiles. Please contact an admin')
    #     return redirect("/")

    try:
        this_profile = FermentationProfile.objects.get(id=profile_id)
    except:
        # The URL contained an invalid profile ID. Redirect to the profile list.
        messages.error(request, 'Invalid profile selected for deletion')
        return redirect('profile_list')

    if not this_profile.is_editable():
        # Due to the way we're implementing fermentation profiles, we don't want any edits to a profile that is
        # currently in use.
        this_profile.status = FermentationProfile.STATUS_PENDING_DELETE
        this_profile.save()
        messages.info(request, 'Profile \'{}\' is currently in use but has been queued for deletion.'.format(this_profile.name))
    else:
        this_profile.delete()
        messages.success(request, 'Profile \'{}\' was not in use, and has been deleted.'.format(this_profile.name))

    return redirect('profile_list')


def profile_undelete(request, profile_id):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.edit_fermentation_profile'):
    #     messages.error(request, 'Your account is not permissioned to edit fermentation profiles. Please contact an admin')
    #     return redirect("/")

    try:
        this_profile = FermentationProfile.objects.get(id=profile_id)
    except:
        # The URL contained an invalid profile ID. Redirect to the profile list.
        messages.error(request, 'Invalid profile selected to save from deletion')
        return redirect('profile_list')

    if this_profile.status == FermentationProfile.STATUS_PENDING_DELETE:
        this_profile.status = FermentationProfile.STATUS_ACTIVE
        this_profile.save()
        messages.success(request, 'Profile \'{}\' has been removed from the queue for deletion.'.format(this_profile.name))
    else:
        messages.info(request, 'Profile \'{}\' was not queued for deletion.'.format(this_profile.name))

    return redirect('profile_list')


