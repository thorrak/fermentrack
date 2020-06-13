from django.shortcuts import render
from django.contrib import messages
from django.shortcuts import redirect
from constance import config
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.core.exceptions import ObjectDoesNotExist

from .models import GenericPushTarget, BrewersFriendPushTarget, BrewfatherPushTarget, ThingSpeakPushTarget, GrainfatherPushTarget

import fermentrack_django.settings as settings

from app.decorators import site_is_configured, gravity_support_enabled

import os, subprocess, datetime, pytz, json, logging

import external_push.forms as forms

logger = logging.getLogger(__name__)


@login_required
@site_is_configured
def external_push_list(request, context_only=False):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.add_device'):
    #     messages.error(request, 'Your account is not permissioned to add devices. Please contact an admin')
    #     return redirect("/")

    all_push_targets = GenericPushTarget.objects.all()
    brewers_friend_push_targets = BrewersFriendPushTarget.objects.all()
    brewfather_push_targets = BrewfatherPushTarget.objects.all()
    thingspeak_push_targets = ThingSpeakPushTarget.objects.all()
    grainfather_push_targets = GrainfatherPushTarget.objects.all()

    context = {'all_push_targets': all_push_targets, 'brewfather_push_targets': brewfather_push_targets,
               'brewers_friend_push_targets': brewers_friend_push_targets, 'thingspeak_push_targets': thingspeak_push_targets,
               'grainfather_push_targets': grainfather_push_targets}

    # This allows us to embed this in the site configuration page... There's almost certainly a better way to do this.
    if not context_only:
        return render(request, template_name='external_push/push_target_list.html', context=context)
    else:
        return context



@login_required
@site_is_configured
def external_push_generic_target_add(request):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.add_device'):
    #     messages.error(request, 'Your account is not permissioned to add devices. Please contact an admin')
    #     return redirect("/")

    form = forms.GenericPushTargetModelForm()

    if request.POST:
        form = forms.GenericPushTargetModelForm(request.POST)
        if form.is_valid():
            new_push_target = form.save()
            messages.success(request, 'Successfully added push target')

            # Update last triggered to force a refresh in the next cycle
            new_push_target.last_triggered = new_push_target.last_triggered - datetime.timedelta(seconds=new_push_target.push_frequency)
            new_push_target.save()

            return redirect('external_push_list')

        messages.error(request, 'Unable to add new push target')

    # Basically, if we don't get redirected, in every case we're just outputting the same template
    return render(request, template_name='external_push/generic_push_target_add.html', context={'form': form})


@login_required
@site_is_configured
def external_push_view(request, push_target_id):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.add_device'):
    #     messages.error(request, 'Your account is not permissioned to add devices. Please contact an admin')
    #     return redirect("/")

    try:
        push_target = GenericPushTarget.objects.get(id=push_target_id)
    except ObjectDoesNotExist:
        messages.error(request, "External push target {} does not exist".format(push_target_id))
        return redirect('external_push_list')

    if request.POST:
        form = forms.GenericPushTargetModelForm(request.POST, instance=push_target)
        if form.is_valid():
            updated_push_target = form.save()
            messages.success(request, 'Updated push target')
            return redirect('external_push_list')

        messages.error(request, 'Unable to update push target')


    # TODO - Check if we have models other than GenericPushTarget and adapt accordingly
    form = forms.GenericPushTargetModelForm(instance=push_target)


    return render(request, template_name='external_push/push_target_view.html',
                  context={'push_target': push_target, 'form': form})


@login_required
@site_is_configured
def external_push_delete(request, push_target_id):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.add_device'):
    #     messages.error(request, 'Your account is not permissioned to add devices. Please contact an admin')
    #     return redirect("/")

    try:
        push_target = GenericPushTarget.objects.get(id=push_target_id)
    except ObjectDoesNotExist:
        messages.error(request, "External push target {} does not exist".format(push_target_id))
        return redirect('external_push_list')

    message = 'Push target {} has been deleted'.format(push_target.name)
    push_target.delete()
    messages.success(request, message)

    return redirect('external_push_list')




@login_required
@site_is_configured
def external_push_brewers_friend_target_add(request):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.add_device'):
    #     messages.error(request, 'Your account is not permissioned to add devices. Please contact an admin')
    #     return redirect("/")

    form = forms.BrewersFriendPushTargetModelForm()

    if request.POST:
        form = forms.BrewersFriendPushTargetModelForm(request.POST)
        if form.is_valid():
            new_push_target = form.save()
            messages.success(request, 'Successfully added push target')

            # Update last triggered to force a refresh in the next cycle
            new_push_target.last_triggered = new_push_target.last_triggered - datetime.timedelta(seconds=new_push_target.push_frequency)
            new_push_target.save()

            return redirect('external_push_list')

        messages.error(request, 'Unable to add new push target')

    # Basically, if we don't get redirected, in every case we're just outputting the same template
    return render(request, template_name='external_push/brewers_friend_push_target_add.html', context={'form': form})


@login_required
@site_is_configured
def external_push_brewers_friend_view(request, push_target_id):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.add_device'):
    #     messages.error(request, 'Your account is not permissioned to add devices. Please contact an admin')
    #     return redirect("/")

    try:
        push_target = BrewersFriendPushTarget.objects.get(id=push_target_id)
    except ObjectDoesNotExist:
        messages.error(request, "Brewers's Friend push target {} does not exist".format(push_target_id))
        return redirect('external_push_list')

    if request.POST:
        form = forms.BrewersFriendPushTargetModelForm(request.POST, instance=push_target)
        if form.is_valid():
            updated_push_target = form.save()
            messages.success(request, 'Updated push target')
            return redirect('external_push_list')

        messages.error(request, 'Unable to update push target')

    form = forms.BrewersFriendPushTargetModelForm(instance=push_target)

    return render(request, template_name='external_push/brewers_friend_push_target_view.html',
                  context={'push_target': push_target, 'form': form})


@login_required
@site_is_configured
def external_push_brewers_friend_delete(request, push_target_id):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.add_device'):
    #     messages.error(request, 'Your account is not permissioned to add devices. Please contact an admin')
    #     return redirect("/")

    try:
        push_target = BrewersFriendPushTarget.objects.get(id=push_target_id)
    except ObjectDoesNotExist:
        messages.error(request, "Brewers's Friend push target {} does not exist".format(push_target_id))
        return redirect('external_push_list')

    message = "Brewers's Friend push target {} has been deleted".format(push_target_id)
    push_target.delete()
    messages.success(request, message)

    return redirect('external_push_list')







@login_required
@site_is_configured
def external_push_brewfather_target_add(request):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.add_device'):
    #     messages.error(request, 'Your account is not permissioned to add devices. Please contact an admin')
    #     return redirect("/")

    form = forms.BrewfatherPushTargetModelForm()

    if request.POST:
        form = forms.BrewfatherPushTargetModelForm(request.POST)
        if form.is_valid():
            new_push_target = form.save()
            messages.success(request, 'Successfully added push target')

            # Update last triggered to force a refresh in the next cycle
            new_push_target.last_triggered = new_push_target.last_triggered - datetime.timedelta(seconds=new_push_target.push_frequency)
            new_push_target.save()

            return redirect('external_push_list')

        messages.error(request, 'Unable to add new push target')

    # Basically, if we don't get redirected, in every case we're just outputting the same template
    return render(request, template_name='external_push/brewfather_push_target_add.html', context={'form': form})


@login_required
@site_is_configured
def external_push_brewfather_view(request, push_target_id):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.add_device'):
    #     messages.error(request, 'Your account is not permissioned to add devices. Please contact an admin')
    #     return redirect("/")

    try:
        push_target = BrewfatherPushTarget.objects.get(id=push_target_id)
    except ObjectDoesNotExist:
        messages.error(request, "Brewfather push target {} does not exist".format(push_target_id))
        return redirect('external_push_list')

    if request.POST:
        form = forms.BrewfatherPushTargetModelForm(request.POST, instance=push_target)
        if form.is_valid():
            updated_push_target = form.save()
            messages.success(request, 'Updated push target')
            return redirect('external_push_list')

        messages.error(request, 'Unable to update push target')

    form = forms.BrewfatherPushTargetModelForm(instance=push_target)

    return render(request, template_name='external_push/brewfather_push_target_view.html',
                  context={'push_target': push_target, 'form': form})


@login_required
@site_is_configured
def external_push_brewfather_delete(request, push_target_id):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.add_device'):
    #     messages.error(request, 'Your account is not permissioned to add devices. Please contact an admin')
    #     return redirect("/")

    try:
        push_target = BrewfatherPushTarget.objects.get(id=push_target_id)
    except ObjectDoesNotExist:
        messages.error(request, "Brewfather push target {} does not exist".format(push_target_id))
        return redirect('external_push_list')

    message = "Brewfather push target {} has been deleted".format(push_target_id)
    push_target.delete()
    messages.success(request, message)

    return redirect('external_push_list')




@login_required
@site_is_configured
def external_push_thingspeak_target_add(request):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.add_device'):
    #     messages.error(request, 'Your account is not permissioned to add devices. Please contact an admin')
    #     return redirect("/")

    form = forms.ThingSpeakPushTargetModelForm()

    if request.POST:
        form = forms.ThingSpeakPushTargetModelForm(request.POST)
        if form.is_valid():
            new_push_target = form.save()
            messages.success(request, 'Successfully added push target')

            # Update last triggered to force a refresh in the next cycle
            new_push_target.last_triggered = new_push_target.last_triggered - datetime.timedelta(seconds=new_push_target.push_frequency)
            new_push_target.save()

            return redirect('external_push_list')

        messages.error(request, 'Unable to add new push target')

    # Basically, if we don't get redirected, in every case we're just outputting the same template
    return render(request, template_name='external_push/thingspeak_push_target_add.html', context={'form': form})

@login_required
@site_is_configured
def external_push_thingspeak_view(request, push_target_id):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.add_device'):
    #     messages.error(request, 'Your account is not permissioned to add devices. Please contact an admin')
    #     return redirect("/")

    try:
        push_target = ThingSpeakPushTarget.objects.get(id=push_target_id)
    except ObjectDoesNotExist:
        messages.error(request, "ThingSpeak push target {} does not exist".format(push_target_id))
        return redirect('external_push_list')

    if request.POST:
        form = forms.ThingSpeakPushTargetModelForm(request.POST, instance=push_target)
        if form.is_valid():
            updated_push_target = form.save()
            messages.success(request, 'Updated push target')
            return redirect('external_push_list')

        messages.error(request, 'Unable to update push target')

    form = forms.ThingSpeakPushTargetModelForm(instance=push_target)

    return render(request, template_name='external_push/thingspeak_push_target_view.html',
                  context={'push_target': push_target, 'form': form})

@login_required
@site_is_configured
def external_push_thingspeak_delete(request, push_target_id):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.add_device'):
    #     messages.error(request, 'Your account is not permissioned to add devices. Please contact an admin')
    #     return redirect("/")

    try:
        push_target = ThingSpeakPushTarget.objects.get(id=push_target_id)
    except ObjectDoesNotExist:
        messages.error(request, "ThingSpeak push target {} does not exist".format(push_target_id))
        return redirect('external_push_list')

    message = "ThingSpeak push target {} has been deleted".format(push_target_id)
    push_target.delete()
    messages.success(request, message)

    return redirect('external_push_list')


@login_required
@site_is_configured
def external_push_grainfather_target_add(request):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.add_device'):
    #     messages.error(request, 'Your account is not permissioned to add devices. Please contact an admin')
    #     return redirect("/")

    form = forms.GrainfatherPushTargetModelForm()

    if request.POST:
        form = forms.GrainfatherPushTargetModelForm(request.POST)
        if form.is_valid():
            new_push_target = form.save()
            messages.success(request, 'Successfully added push target')

            # Update last triggered to force a refresh in the next cycle
            new_push_target.last_triggered = new_push_target.last_triggered - datetime.timedelta(seconds=new_push_target.push_frequency)
            new_push_target.save()

            return redirect('external_push_list')

        messages.error(request, 'Unable to add new push target')

    # Basically, if we don't get redirected, in every case we're just outputting the same template
    return render(request, template_name='external_push/grainfather_push_target_add.html', context={'form': form})


@login_required
@site_is_configured
def external_push_grainfather_view(request, push_target_id):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.add_device'):
    #     messages.error(request, 'Your account is not permissioned to add devices. Please contact an admin')
    #     return redirect("/")

    try:
        push_target = GrainfatherPushTarget.objects.get(id=push_target_id)
    except ObjectDoesNotExist:
        messages.error(request, "Grainfather push target {} does not exist".format(push_target_id))
        return redirect('external_push_list')

    if request.POST:
        form = forms.GrainfatherPushTargetModelForm(request.POST, instance=push_target)
        if form.is_valid():
            updated_push_target = form.save()
            messages.success(request, 'Updated push target')
            return redirect('external_push_list')

        messages.error(request, 'Unable to update push target')

    form = forms.GrainfatherPushTargetModelForm(instance=push_target)

    return render(request, template_name='external_push/grainfather_push_target_view.html',
                  context={'push_target': push_target, 'form': form})


@login_required
@site_is_configured
def external_push_grainfather_delete(request, push_target_id):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.add_device'):
    #     messages.error(request, 'Your account is not permissioned to add devices. Please contact an admin')
    #     return redirect("/")

    try:
        push_target = GrainfatherPushTarget.objects.get(id=push_target_id)
    except ObjectDoesNotExist:
        messages.error(request, "Grainfather push target {} does not exist".format(push_target_id))
        return redirect('external_push_list')

    message = "Grainfather push target {} has been deleted".format(push_target_id)
    push_target.delete()
    messages.success(request, message)

    return redirect('external_push_list')



