from django.shortcuts import render
from django.contrib import messages
from django.shortcuts import render_to_response, redirect
from django.contrib.auth import login
from django.contrib.auth.models import User
from constance import config
from django.contrib.auth.decorators import login_required

import setup_forms, device_forms
import mdnsLocator

from app.models import BrewPiDevice

from decorators import site_is_configured  # Checks if user has completed constance configuration


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
    num_users = User.objects.all().count()

    # We might want to create CRUD for users later, but it shouldn't be part of the guided setup. If a user has
    # already been created, redirect back to siteroot.
    if num_users > 0:
        messages.error(request, 'Cannot use guided setup to create multiple users - use the <a href="/admin/">admin ' +
                                'portal</a> instead.')
        return redirect('siteroot')

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


@login_required
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
#     Select connection type (serial_wifi) *OR* if device doesn't support WiFi, redirect as "serial"
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

@login_required
@site_is_configured
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


@login_required
@site_is_configured
def device_guided_flash_prompt(request, device_family):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.add_device'):
    #     messages.error(request, 'Your account is not permissioned to add devices. Please contact an admin')
    #     return redirect("/")

    can_flash_family = False
    serial_only_families = ['Arduino', 'Spark', 'Fuscus']

    if request.POST:
        form = setup_forms.GuidedDeviceFlashForm(request.POST)
        if form.is_valid():
            if not form.cleaned_data['should_flash_device']:
                if form.cleaned_data['device_family'] in serial_only_families:
                    # TODO - Redirect this to the actual serial autodetect script once complete
                    # The device doesn't support both serial and wifi. Redirect to the serial flow.
                    return redirect('device_guided_serial_wifi', device_family=form.cleaned_data['device_family'])
                else:
                    # The device can connect via either serial or wifi. prompt
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


@login_required
@site_is_configured
def device_guided_serial_wifi(request, device_family):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.add_device'):
    #     messages.error(request, 'Your account is not permissioned to add devices. Please contact an admin')
    #     return redirect("/")

    return render_with_devices(request, template_name='setup/device_guided_serial_wifi.html',
                               context={'device_family': device_family})


@login_required
@site_is_configured
def device_guided_find_mdns(request):
    installed_devices, available_devices = mdnsLocator.find_mdns_devices()

    return render_with_devices(request, template_name="setup/device_guided_mdns_locate.html",
                               context={'installed_devices': installed_devices,
                                        'available_devices': available_devices})


@login_required
@site_is_configured
def device_guided_add_mdns(request, mdns_id):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.add_device'):
    #     messages.error(request, 'Your account is not permissioned to add devices. Please contact an admin')
    #     return redirect("/")

    # Originally I thought we needed to rescan the network, but so long as ESP8266 is the only device that supports WiFi
    # We can use mdns_id alone to handle the initial values

    # installed_devices, available_devices = mdnsLocator.find_mdns_devices()
    #
    # mdns_device = None
    #
    # for this_device in available_devices:
    #     if this_device['mDNSname'] == mdns_id:
    #         mdns_device = this_device
    #
    # if mdns_device is None:
    #     redirect('device_guided_mdns')


    if request.POST:
        form = device_forms.DeviceForm(request.POST)
        if form.is_valid():
            new_device = BrewPiDevice(
                device_name=form.cleaned_data['device_name'],
                temp_format=form.cleaned_data['temp_format'],
                data_point_log_interval=form.cleaned_data['data_point_log_interval'],
                useInetSocket=form.cleaned_data['useInetSocket'],
                socketPort=form.cleaned_data['socketPort'],
                socketHost=form.cleaned_data['socketHost'],
                serial_port=form.cleaned_data['serial_port'],
                serial_alt_port=form.cleaned_data['serial_alt_port'],
                board_type=form.cleaned_data['board_type'],
                socket_name=form.cleaned_data['socket_name'],
                connection_type=form.cleaned_data['connection_type'],
                wifi_host=form.cleaned_data['wifi_host'],
                wifi_port=form.cleaned_data['wifi_port'],
            )

            new_device.save()

            messages.success(request, 'Device {} Added'.format(new_device.device_name))
            return redirect("/")

        else:
            return render_with_devices(request, template_name='setup/device_guided_add_mdns.html', context={'form': form})
    else:
        # If we were just passed to the form, provide the initial values
        initial_values = {'board_type': 'esp8266', 'wifi_host': mdns_id, 'wifi_port': 23, 'connection_type': 'wifi'}

        form = device_forms.DeviceForm(initial=initial_values)
        return render_with_devices(request, template_name='setup/device_guided_add_mdns.html', context={'form': form})

