from django.shortcuts import render
from django.contrib import messages
from django.shortcuts import render_to_response, redirect
from django.contrib.auth import login
from django.contrib.auth.models import User
from constance import config

import setup_forms

def setup_guided_add_user(request):
    # TODO - When app is configured, only super users should only get here
    if request.POST:
        form = setup_forms.GuidedSetupUserForm(request.POST)
        if form.is_valid():
            new_user = form.save(commit=False)
            new_user.is_superuser = True
            new_user.is_staff = True
            new_user.save()
            #new_user_creaed = User.objects.create_user(**form.cleaned_data)
            # We login the user right away
            login(request, new_user)
            return redirect('setup_guided_config')
        else:
            return render(request, template_name='setup_guided_add_user.html', context={'form': form})
    else:
        form = setup_forms.GuidedSetupUserForm()
        return render(request, template_name='setup_guided_add_user.html', context={'form': form})


def setup_guided_config(request):
    # TODO - Add user permissioning, the wizard creates the user and login
    # the user so it should be safe to check for super-user here.
    if request.POST:
        form = setup_forms.GuidedSetupConfigForm(request.POST)
        if form.is_valid():
            f = form.cleaned_data
            config.BREWERY_NAME = f['brewery_name']
            config.DATE_TIME_FORMAT = f['date_time_format']
            config.DATE_TIME_FORMAT_DISPLAY = f['date_time_format_display']
            config.REQUIRE_LOGIN_FOR_DASHBOARD = f['require_login_for_dashboard']
            config.TEMPERATURE_FORMAT = f['temperature_format']
            return redirect('siteroot')
        else:
            return render(request, template_name='setup_guided_config.html', context={'form': form})
    else:
        form = setup_forms.GuidedSetupConfigForm()
        return render(request, template_name='setup_guided_config.html', context={'form': form})