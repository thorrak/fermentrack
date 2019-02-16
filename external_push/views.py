from django.shortcuts import render
from django.contrib import messages
from django.shortcuts import render_to_response, redirect
from constance import config
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.core.exceptions import ObjectDoesNotExist

from .models import GenericPushTarget

import fermentrack_django.settings as settings

from app.decorators import site_is_configured, gravity_support_enabled

import os, subprocess, datetime, pytz, json, logging

import external_push.forms as forms

logger = logging.getLogger(__name__)


@login_required
@site_is_configured
def external_push_list(request):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.add_device'):
    #     messages.error(request, 'Your account is not permissioned to add devices. Please contact an admin')
    #     return redirect("/")

    all_push_targets = GenericPushTarget.objects.all()

    return render(request, template_name='external_push/push_target_list.html',
                  context={'all_push_targets': all_push_targets})



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
            # new_push_target = form.save(commit=False)
            # new_push_target.save()

            messages.success(request, 'Successfully added push target')

            return redirect('gravity_list')

        messages.error(request, 'Unable to add new push target')

    # Basically, if we don't get redirected, in every case we're just outputting the same template
    return render(request, template_name='external_push/generic_push_target_add.html', context={'form': form})


