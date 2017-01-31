from django.shortcuts import render
from django.contrib import messages
from django.shortcuts import render_to_response, redirect

from constance import config  # For the explicitly user-configurable stuff

import device_forms
import profile_forms
import mdnsLocator

import json, time


from app.models import BrewPiDevice, OldControlConstants, NewControlConstants, PinDevice, SensorDevice, BeerLogPoint, FermentationProfile

def render_with_devices(request, template_name, context=None, content_type=None, status=None, using=None):
    all_devices = BrewPiDevice.objects.all()
    # TODO - Delete once we're confirmed to no longer be using InstallSettings
    # site_config = InstallSettings.objects.all()
    if context:  # Append to the context dict if it exists, otherwise create the context dict to add
        context['all_devices'] = all_devices
    else:
        context={'all_devices': all_devices}
    # if len(site_config)>1:  # TODO - Make this grab the first siteconfig
    #     context['site_config'] = site_config

    return render(request, template_name, context, content_type, status, using)

#
# The general flow of guided setup looks like this:
#   Select device family (select_device)
#     |
#     Need to flash? (And we can flash) (device_flash)
#     |       |
#     | No    | Yes
#     |
#     |
#     |

def device_guided_select_device(request):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.add_device'):
    #     messages.error(request, 'Your account is not permissioned to add devices. Please contact an admin')
    #     return redirect("/")

    if request.POST:
        form = device_forms.GuidedDeviceSelectForm(request.POST)
        if form.is_valid():
            return redirect('device_guided_flash_prompt', device_family=form.cleaned_data['device_family'])
        else:
            return render_with_devices(request, template_name='device_guided_select_device.html', context={'form': form})
    else:
        form = device_forms.GuidedDeviceSelectForm()
        return render_with_devices(request, template_name='device_guided_select_device.html', context={'form': form})


def device_guided_flash_prompt(request, device_family):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.add_device'):
    #     messages.error(request, 'Your account is not permissioned to add devices. Please contact an admin')
    #     return redirect("/")

    can_flash_family = False

    if request.POST:
        form = device_forms.GuidedDeviceFlashForm(request.POST)
        if form.is_valid():
            if not form.cleaned_data['should_flash_device']:
                return redirect('device_guided_serial_wifi', device_family=form.cleaned_data['device_family'])
            else:
                # TODO - Actually flash the device
                return redirect('device_guided_flash_prompt', device_family=form.cleaned_data['device_family'])
        else:
            return render_with_devices(request, template_name='device_guided_flash_prompt.html',
                                       context={'form': form, 'device_family': device_family,
                                                'can_flash_family': can_flash_family})
    else:
        form = device_forms.GuidedDeviceFlashForm()
        return render_with_devices(request, template_name='device_guided_flash_prompt.html',
                                   context={'form': form, 'device_family': device_family,
                                            'can_flash_family': can_flash_family})


def device_guided_serial_wifi(request, device_family):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.add_device'):
    #     messages.error(request, 'Your account is not permissioned to add devices. Please contact an admin')
    #     return redirect("/")

    return render_with_devices(request, template_name='device_guided_serial_wifi.html',
                               context={'device_family': device_family})

