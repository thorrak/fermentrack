from django.shortcuts import render
from django.contrib import messages
from django.shortcuts import render_to_response, redirect
from django.contrib.auth import login
from django.contrib.auth.models import User
from constance import config

import setup_forms

from app.models import BrewPiDevice


def render_with_devices(request, template_name, context=None, content_type=None, status=None, using=None):
    all_devices = BrewPiDevice.objects.all()

    if context:  # Append to the context dict if it exists, otherwise create the context dict to add
        context['all_devices'] = all_devices
    else:
        context={'all_devices': all_devices}

    return render(request, template_name, context, content_type, status, using)


###################################################################################################################
# Initial Setup Views
###################################################################################################################


def setup_add_user(request):
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
            messages.success(request, 'User {} created and logged in successfully'.format(new_user.username))
            return redirect('setup_config')
        else:
            return render(request, template_name='setup/setup_add_user.html', context={'form': form})
    else:
        form = setup_forms.GuidedSetupUserForm()
        return render(request, template_name='setup/setup_add_user.html', context={'form': form})


def setup_config(request):
    # TODO - Add user permissioning. The wizard creates the user and login so we can check for superuser here
    if request.POST:
        form = setup_forms.GuidedSetupConfigForm(request.POST)
        if form.is_valid():
            f = form.cleaned_data
            config.BREWERY_NAME = f['brewery_name']
            config.DATE_TIME_FORMAT = f['date_time_format']
            config.DATE_TIME_FORMAT_DISPLAY = f['date_time_format_display']
            config.REQUIRE_LOGIN_FOR_DASHBOARD = f['require_login_for_dashboard']
            config.TEMPERATURE_FORMAT = f['temperature_format']
            config.USER_HAS_COMPLETED_CONFIGURATION = True  # Toggle once they've completed the configuration workflow
            messages.success(request, 'App configuration has been saved')
            return redirect('siteroot')
        else:
            return render_with_devices(request, template_name='setup/setup_config.html',
                                       context={'form': form,
                                                'completed_config': config.USER_HAS_COMPLETED_CONFIGURATION})
    else:
        form = setup_forms.GuidedSetupConfigForm()
        return render_with_devices(request, template_name='setup/setup_config.html',
                                   context={'form': form,
                                            'completed_config': config.USER_HAS_COMPLETED_CONFIGURATION})


def setup_splash(request):
    # Send the number of users we got in the system as a way to know if this is the first run or not.
    context={'num_users': User.objects.all().count(), 'completed_config': config.USER_HAS_COMPLETED_CONFIGURATION}
    return render_with_devices(request, template_name="setup/setup_unconfigured_splash.html", context=context)


###################################################################################################################
# Guided Setup Views
###################################################################################################################


#
# The general flow of guided setup looks like this:
#   Select device family (select_device)
#     |
#     Need to flash? (And we can flash) (device_flash)
#     |       |
#     | No    | Yes
#     |       |
#     |       Redirect to flash device (TODO)
#     |       |
#     Select connection type
#     |       |
#     | WiFi  | Serial
#     |       \-------------------\
#     |                           |
#     mDNS Device Selection       |
#     |                           |
#     |       /-------------------/
#     |       |
#     |       Serial Device Autodetection
#     |       |
#     |       |
#     Preload device details & set up

def device_guided_select_device(request):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.add_device'):
    #     messages.error(request, 'Your account is not permissioned to add devices. Please contact an admin')
    #     return redirect("/")

    if request.POST:
        form = setup_forms.GuidedDeviceSelectForm(request.POST)
        if form.is_valid():
            return redirect('device_guided_flash_prompt', device_family=form.cleaned_data['device_family'])
        else:
            return render_with_devices(request, template_name='setup/device_guided_select_device.html', context={'form': form})
    else:
        form = setup_forms.GuidedDeviceSelectForm()
        return render_with_devices(request, template_name='setup/device_guided_select_device.html', context={'form': form})


def device_guided_flash_prompt(request, device_family):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.add_device'):
    #     messages.error(request, 'Your account is not permissioned to add devices. Please contact an admin')
    #     return redirect("/")

    can_flash_family = False

    if request.POST:
        form = setup_forms.GuidedDeviceFlashForm(request.POST)
        if form.is_valid():
            if not form.cleaned_data['should_flash_device']:
                return redirect('device_guided_serial_wifi', device_family=form.cleaned_data['device_family'])
            else:
                # TODO - Actually flash the device
                return redirect('device_guided_flash_prompt', device_family=form.cleaned_data['device_family'])
        else:
            return render_with_devices(request, template_name='setup/device_guided_flash_prompt.html',
                                       context={'form': form, 'device_family': device_family,
                                                'can_flash_family': can_flash_family})
    else:
        form = setup_forms.GuidedDeviceFlashForm()
        return render_with_devices(request, template_name='setup/device_guided_flash_prompt.html',
                                   context={'form': form, 'device_family': device_family,
                                            'can_flash_family': can_flash_family})


def device_guided_serial_wifi(request, device_family):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.add_device'):
    #     messages.error(request, 'Your account is not permissioned to add devices. Please contact an admin')
    #     return redirect("/")

    return render_with_devices(request, template_name='setup/device_guided_serial_wifi.html',
                               context={'device_family': device_family})

