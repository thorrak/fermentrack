from django.shortcuts import render
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from constance import config
# Checks if user has completed constance configuration
from .decorators import site_is_configured
from django.http import HttpResponse
from app.models import BrewPiDevice, FermentationProfilePoint, FermentationProfile
from . import device_forms, profile_forms
import json, time, csv, pytz
from datetime import datetime
from django.utils import timezone


@login_required
@site_is_configured
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
            return render(request, template_name='profile/profile_new.html', context={'form': form})
    else:
        form = profile_forms.FermentationProfileForm()
        return render(request, template_name='profile/profile_new.html', context={'form': form})


@login_required
@site_is_configured
def profile_edit(request, profile_id):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.edit_fermentation_profile'):
    #     messages.error(request, 'Your account is not permissioned to edit fermentation profiles. Please contact an admin')
    #     return redirect("/")
    try:
        this_profile = FermentationProfile.objects.get(id=profile_id)
        this_profile_points = this_profile.fermentationprofilepoint_set.order_by('ttl')
    except:
        # The URL contained an invalid profile ID. Redirect to the profile
        # list.
        messages.error(request, 'Invalid profile \'{}\' selected for editing'.format(profile_id))
        return redirect('profile_list')

    rename_form = profile_forms.FermentationProfileRenameForm(initial={'profile_name': this_profile.name})

    if request.POST:
        form = profile_forms.FermentationProfilePointForm(request.POST)
        if form.is_valid():
            new_profile_point = FermentationProfilePoint(
                profile=this_profile,
                ttl=form.cleaned_data['ttl'],
                temperature_setting=form.cleaned_data['temperature_setting'],
                # Arguably, I could add this to the form
                temp_format=config.TEMPERATURE_FORMAT,
            )
            new_profile_point.save()
            this_profile_points = FermentationProfilePoint.objects.filter(
                profile=this_profile
            ).order_by('ttl')
            # Regardless of whether we were successful or not - rerender the
            # existing edit page
        return render(request, template_name='profile/profile_edit.html',
                      context={'form': form, 'this_profile': this_profile, 'rename_form': rename_form,
                               'this_profile_points': this_profile_points})
    else:
        form = profile_forms.FermentationProfilePointForm()
        return render(request, template_name='profile/profile_edit.html',
                      context={'form': form, 'this_profile': this_profile, 'rename_form': rename_form,
                               'this_profile_points': this_profile_points})


@login_required
@site_is_configured
def profile_list(request):
    # There must be a better way to implement cleaning up profiles pending
    # deletion...
    FermentationProfile.cleanup_pending_delete()
    all_profiles = FermentationProfile.objects.all()
    return render(request, template_name='profile/profile_list.html', context={'all_profiles': all_profiles})


@login_required
@site_is_configured
def profile_setpoint_delete(request, profile_id, point_id):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.edit_fermentation_profile'):
    #     messages.error(request, 'Your account is not permissioned to edit fermentation profiles. Please contact an admin')
    #     return redirect("/")
    try:
        this_profile_point = FermentationProfilePoint.objects.get(id=point_id)
    except:
        # The URL contained an invalid profile ID. Redirect to the profile
        # list.
        messages.error(
            request, 'Invalid profile setpoint selected for deletion')
        return redirect('profile_edit', profile_id=profile_id)

    if not this_profile_point.profile.is_editable():
        # Due to the way we're implementing fermentation profiles, we don't want any edits (including deletion of
        # points!) to a profile that is currently in use.
        messages.error(
            request, 'Unable to edit a fermentation profile that is currently in use')
    else:
        this_profile_point.delete()
        messages.success(request, 'Setpoint deleted')

    return redirect('profile_edit', profile_id=profile_id)


@login_required
@site_is_configured
def profile_delete(request, profile_id):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.edit_fermentation_profile'):
    #     messages.error(request, 'Your account is not permissioned to edit fermentation profiles. Please contact an admin')
    #     return redirect("/")
    try:
        this_profile = FermentationProfile.objects.get(id=profile_id)
    except:
        # The URL contained an invalid profile ID. Redirect to the profile
        # list.
        messages.error(request, 'Invalid profile selected for deletion')
        return redirect('profile_list')

    if not this_profile.is_editable():
        # Due to the way we're implementing fermentation profiles, we don't want any edits to a profile that is
        # currently in use.
        this_profile.status = FermentationProfile.STATUS_PENDING_DELETE
        this_profile.save()
        messages.info(request,
                      'Profile \'{}\' is currently in use but has been queued for deletion.'.format(this_profile.name))
    else:
        this_profile.delete()
        messages.success(request, 'Profile \'{}\' was not in use, and has been deleted.'.format(this_profile.name))

    return redirect('profile_list')


@login_required
@site_is_configured
def profile_undelete(request, profile_id):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.edit_fermentation_profile'):
    #     messages.error(request, 'Your account is not permissioned to edit fermentation profiles. Please contact an admin')
    #     return redirect("/")
    try:
        this_profile = FermentationProfile.objects.get(id=profile_id)
    except:
        # The URL contained an invalid profile ID. Redirect to the profile
        # list.
        messages.error(request, 'Invalid profile selected to save from deletion')
        return redirect('profile_list')

    if this_profile.status == FermentationProfile.STATUS_PENDING_DELETE:
        this_profile.status = FermentationProfile.STATUS_ACTIVE
        this_profile.save()
        messages.success(request,
                         'Profile \'{}\' has been removed from the queue for deletion.'.format(this_profile.name))
    else:
        messages.info(request, 'Profile \'{}\' was not previously queued for deletion and has not been updated.'.format(this_profile.name))

    return redirect('profile_list')


@login_required
@site_is_configured
def profile_points_to_csv(request, profile_id):
    # profile_points_to_csv is used exclusively for displaying a graph of fermentation profiles on the profile edit
    # page

    preferred_tz = pytz.timezone(config.PREFERRED_TIMEZONE)

    profile = FermentationProfile.objects.get(id=profile_id)
    profile_points = profile.fermentationprofilepoint_set.order_by('ttl')
    response = HttpResponse(content_type='text/plain')
    writer = csv.writer(response)
    writer.writerow(['date', 'temp'])
    # If the profile's first point is in the future, add an additional point for today showing the temperature will be
    # held constant until that first point's ttl is reached.
    if profile_points[0].ttl != 0:
        writer.writerow(["{:%Y/%m/%d %X}".format(timezone.now().astimezone(preferred_tz)), profile_points[0].temp_to_preferred()])
    for p in profile_points:
        profilepoint_date = "{:%Y/%m/%d %X}".format(timezone.now().astimezone(preferred_tz) + p.ttl)
        writer.writerow([profilepoint_date, p.temp_to_preferred()])
    return response



@login_required
@site_is_configured
def profile_import(request):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.add_fermentation_profile'):
    #     messages.error(request, 'Your account is not permissioned to add fermentation profiles. Please contact an admin')
    #     return redirect("/")
    if request.POST:
        form = profile_forms.FermentationProfileImportForm(request.POST)
        if form.is_valid():
            try:
                new_profile = FermentationProfile.import_from_text(form.cleaned_data['import_text'])
                messages.success(request, u'New fermentation profile \'{}\' imported'.format(new_profile.name))

                return redirect('profile_edit', profile_id=new_profile.id)

            except ValueError as err:
                messages.error(request, u"Import Error: " + err.message)
                return render(request, template_name='profile/profile_import.html', context={'form': form})

        else:
            return render(request, template_name='profile/profile_import.html', context={'form': form})
    else:
        form = profile_forms.FermentationProfileImportForm()
        return render(request, template_name='profile/profile_import.html', context={'form': form})



@login_required
@site_is_configured
def profile_copy(request, profile_id):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.add_fermentation_profile'):
    #     messages.error(request, 'Your account is not permissioned to add fermentation profiles. Please contact an admin')
    #     return redirect("/")
    try:
        this_profile = FermentationProfile.objects.get(id=profile_id)
    except:
        # The URL contained an invalid profile ID. Redirect to the profile list.
        messages.error(request, 'Invalid source profile to copy')
        return redirect('profile_list')

    if request.POST:
        form = profile_forms.FermentationProfileCopyForm(request.POST)
        if form.is_valid():
            try:
                new_profile = this_profile.copy_to_new(form.cleaned_data['new_profile_name'])
                messages.success(request, u'Fermentation profile copied to \'{}\''.format(new_profile.name))

                return redirect('profile_edit', profile_id=new_profile.id)

            except ValueError as err:
                messages.error(request, u"Copy Error: " + err.message)
                return render(request, template_name='profile/profile_copy.html',
                              context={'form': form, 'this_profile': this_profile})

        else:
            return render(request, template_name='profile/profile_copy.html',
                          context={'form': form, 'this_profile': this_profile})
    else:
        form = profile_forms.FermentationProfileCopyForm()
        return render(request, template_name='profile/profile_copy.html',
                      context={'form': form, 'this_profile': this_profile})


@login_required
@site_is_configured
def profile_rename(request, profile_id):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.add_fermentation_profile'):
    #     messages.error(request, 'Your account is not permissioned to add fermentation profiles. Please contact an admin')
    #     return redirect("/")
    try:
        this_profile = FermentationProfile.objects.get(id=profile_id)
    except:
        # The URL contained an invalid profile ID. Redirect to the profile list.
        messages.error(request, u'Unable to locate profile with ID {}'.format(profile_id))
        return redirect('profile_list')

    if request.POST:
        form = profile_forms.FermentationProfileRenameForm(request.POST)
        if form.is_valid():
            this_profile.name = form.cleaned_data['profile_name']
            this_profile.save()
            messages.success(request, u"Successfully renamed fermentation profile")
            return redirect('profile_edit', profile_id=profile_id)
        else:
            messages.error(request, u"The new name specified was invalid")
            return redirect('profile_edit', profile_id=profile_id)
    else:
        messages.error(request, u"No new profile name was specified")
        return redirect('profile_edit', profile_id=profile_id)
