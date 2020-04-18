from django.shortcuts import render
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth import login
from django.contrib.auth.models import User
from constance import config
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.conf import settings

from . import setup_forms, device_forms
from . import mdnsLocator, serial_integration

from app.models import BrewPiDevice

from .decorators import site_is_configured  # Checks if user has completed constance configuration
import random, configparser


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
            if config.USER_HAS_COMPLETED_CONFIGURATION:
                return redirect('siteroot')
            else:
                return redirect('setup_config')
        else:
            return render(request, template_name='setup/setup_add_user.html', context={'form': form})
    else:
        form = setup_forms.GuidedSetupUserForm()
        return render(request, template_name='setup/setup_add_user.html', context={'form': form})


def set_sentry_status(enabled=True):
    config = configparser.ConfigParser()
    config.read(settings.CONFIG_INI_FILEPATH)
    config['sentry'] = {}

    if enabled:
        config['sentry']['enable_sentry'] = 'yes'
    else:
        config['sentry']['enable_sentry'] = 'no'

    with open(settings.CONFIG_INI_FILEPATH, 'w') as configfile:
        config.write(configfile)


@login_required
def setup_config(request):
    # TODO - Add user permissioning. The wizard creates the user and login so we can check for superuser here
    if request.POST:
        form = setup_forms.GuidedSetupConfigForm(request.POST)
        if form.is_valid():
            f = form.cleaned_data
            config.BREWERY_NAME = f['brewery_name']
            config.DATE_TIME_FORMAT_DISPLAY = f['date_time_format_display']
            config.REQUIRE_LOGIN_FOR_DASHBOARD = f['require_login_for_dashboard']
            config.TEMPERATURE_FORMAT = f['temperature_format']
            config.USER_HAS_COMPLETED_CONFIGURATION = True  # Toggle once they've completed the configuration workflow
            config.PREFERRED_TIMEZONE = f['preferred_timezone']
            config.GRAVITY_SUPPORT_ENABLED = f['enable_gravity_support']
            config.GIT_UPDATE_TYPE = f['update_preference']

            if f['enable_sentry_support'] != settings.ENABLE_SENTRY:
                # The user changed the "Enable Sentry" value - but this doesn't actually take effect until Fermentrack
                # restarts.
                # TODO - Queue a request to Huey to restart fermentrack
                messages.warning(request, "Sentry status has changed - please restart Fermentrack for this to take "
                                          "effect. (This is most easily accomplished by restarting the device running"
                                          "Fermentrack)")

            # This sits outside the if check above in case the user updates the setting before Fermentrack was restarted
            if f['enable_sentry_support']:
                set_sentry_status(enabled=True)
            else:
                set_sentry_status(enabled=False)

            messages.success(request, 'App configuration has been saved')
            return redirect('siteroot')
        else:
            return render(request, template_name='setup/setup_config.html',
                          context={'form': form, 'completed_config': config.USER_HAS_COMPLETED_CONFIGURATION})
    else:
        form = setup_forms.GuidedSetupConfigForm()
        return render(request, template_name='setup/setup_config.html',
                      context={'form': form, 'completed_config': config.USER_HAS_COMPLETED_CONFIGURATION})


def setup_splash(request):
    # Send the number of users we got in the system as a way to know if this is the first run or not.
    context={'num_users': User.objects.all().count(), 'completed_config': config.USER_HAS_COMPLETED_CONFIGURATION}
    return render(request, template_name="setup/setup_unconfigured_splash.html", context=context)


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
#     |       Redirect to flash device
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
            return render(request, template_name='setup/device_guided_select_device.html', context={'form': form})
    else:
        form = setup_forms.GuidedDeviceSelectForm()
        return render(request, template_name='setup/device_guided_select_device.html', context={'form': form})


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
                    # The device doesn't support both serial and wifi. Redirect to the serial flow.
                    return redirect('device_guided_serial_autodetect', device_family=form.cleaned_data['device_family'])
                else:
                    # The device can connect via either serial or wifi. prompt
                    return redirect('device_guided_serial_wifi', device_family=form.cleaned_data['device_family'])
            else:
                # I don't think this really will ever get called...
                return redirect('device_guided_flash_prompt', device_family=form.cleaned_data['device_family'])
        else:
            return render(request, template_name='setup/device_guided_flash_prompt.html',
                                       context={'form': form, 'device_family': device_family,
                                                'can_flash_family': can_flash_family})
    else:
        form = setup_forms.GuidedDeviceFlashForm()
        return render(request, template_name='setup/device_guided_flash_prompt.html',
                                   context={'form': form, 'device_family': device_family,
                                            'can_flash_family': can_flash_family})


@login_required
@site_is_configured
def device_guided_serial_wifi(request, device_family):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.add_device'):
    #     messages.error(request, 'Your account is not permissioned to add devices. Please contact an admin')
    #     return redirect("/")

    return render(request, template_name='setup/device_guided_serial_wifi.html',
                               context={'device_family': device_family})


@login_required
@site_is_configured
def device_guided_find_mdns(request):
    installed_devices, available_devices = mdnsLocator.find_mdns_devices()

    return render(request, template_name="setup/device_guided_mdns_locate.html",
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

            messages.success(request, u'Device {} Added. Please wait a few seconds for controller to start'.format(new_device))
            return redirect("/")

        else:
            return render(request, template_name='setup/device_guided_add_mdns.html', context={'form': form})
    else:
        random_port = random.randint(2000,3000)
        # If we were just passed to the form, provide the initial values
        initial_values = {'board_type': 'esp8266', 'wifi_host': mdns_id, 'wifi_port': 23, 'connection_type': 'wifi',
                          'socketPort': random_port, 'temp_format': config.TEMPERATURE_FORMAT,
                          'modify_not_create': False}

        form = device_forms.DeviceForm(initial=initial_values)
        return render(request, template_name='setup/device_guided_add_mdns.html', context={'form': form})




@login_required
@site_is_configured
def device_guided_serial_autodetect(request, device_family):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.add_device'):
    #     messages.error(request, 'Your account is not permissioned to add devices. Please contact an admin')
    #     return redirect("/")

    # device_guided_serial_autodetect contains all 4 steps in the Serial autodetection guided setup.

    if not request.POST:
        # If we haven't had something posted to us, provide the instructions page. (Step 1)
        return render(request, template_name='setup/device_guided_serial_autodetect_1.html', context={'device_family': device_family})

    else:
        # Something was posted - figure out what step we're on by looking at the "step" field
        if 'step' not in request.POST:
            # We received a form, but not the right form. Redirect to the start of the autodetection flow.
            return render(request, template_name='setup/device_guided_serial_autodetect_1.html',
                                       context={'device_family': device_family})
        elif request.POST['step'] == "2":
            # Step 2 - Cache the current devices & present the next set of instructions to the user
            current_devices = serial_integration.cache_current_devices()
            return render(request, template_name='setup/device_guided_serial_autodetect_2.html',
                                       context={'device_family': device_family, 'current_devices': current_devices})
        elif request.POST['step'] == "3":
            # Step 3 - Detect newly-connected devices & prompt the user to select the one that corresponds to the
            # device they want to configure.
            _, _, _, new_devices_enriched = serial_integration.compare_current_devices_against_cache(device_family)
            return render(request, template_name='setup/device_guided_serial_autodetect_3.html',
                                       context={'device_family': device_family, 'new_devices': new_devices_enriched})
        elif request.POST['step'] == "4":
            # Step 4 - MAGIC.
            if 'serial_port' in request.POST:
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
                        prefer_connecting_via_udev=form.cleaned_data['prefer_connecting_via_udev'],
                    )

                    new_device.save()

                    # Once the device is added, go ahead and autodetect the udev serial number.
                    if new_device.connection_type == BrewPiDevice.CONNECTION_SERIAL:
                        new_device.set_udev_from_port()

                    messages.success(request, u'Device {} Added. Please wait a few seconds for controller to start'.format(new_device))
                    return redirect("/")

                else:
                    return render(request, template_name='setup/device_guided_serial_autodetect_4_add.html',
                                               context={'form': form, 'device_family': device_family})
            else:
                random_port = random.randint(2000,3000)
                # If we were just passed to the form, provide the initial values
                # TODO - Correctly determine 'board_type'
                if device_family == 'ESP8266':
                    board_type = 'esp8266'
                elif device_family == 'Arduino':
                    board_type = 'uno'
                else:
                    # Invalid board type - shouldn't ever get here.
                    messages.error(request, "Invalid board type for serial autodetection")
                    return redirect("/")

                initial_values = {'board_type': board_type, 'serial_port': request.POST['device'], 'connection_type': 'serial',
                                  'socketPort': random_port, 'temp_format': config.TEMPERATURE_FORMAT,
                                  'modify_not_create': False}

                form = device_forms.DeviceForm(initial=initial_values)
                return render(request, template_name='setup/device_guided_serial_autodetect_4_add.html',
                                           context={'form': form, 'device_family': device_family})

        elif request.POST['step'] == "5":
            pass
        else:
            # The step number we received was invalid. Redirect to the start of the autodetection flow.
            return render(request, template_name='setup/device_guided_serial_autodetect_1.html',
                                       context={'device_family': device_family})



