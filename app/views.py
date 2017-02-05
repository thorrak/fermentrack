from django.shortcuts import render
from django.contrib import messages
from django.shortcuts import render_to_response, redirect

from constance import config  # For the explicitly user-configurable stuff

import device_forms, profile_forms
import setup_views

import mdnsLocator

import json, datetime, pytz

import git_integration
import subprocess

import brewpi_django.settings as settings



from app.models import BrewPiDevice, OldControlConstants, NewControlConstants, PinDevice, SensorDevice, BeerLogPoint, FermentationProfile

def render_with_devices(request, template_name, context=None, content_type=None, status=None, using=None):
    all_devices = BrewPiDevice.objects.all()

    if context:  # Append to the context dict if it exists, otherwise create the context dict to add
        context['all_devices'] = all_devices
    else:
        context={'all_devices': all_devices}

    return render(request, template_name, context, content_type, status, using)


# Siteroot is a lazy way of determining where to direct the user when they go to http://devicename.local/
def siteroot(request):
    # Check the git status at least every 18 hours
    now_time = pytz.timezone(settings.TIME_ZONE).localize(datetime.datetime.now())
    if config.LAST_GIT_CHECK < now_time + datetime.timedelta(hours=18):
        if git_integration.app_is_current():
            config.LAST_GIT_CHECK = now_time
        else:
            messages.info(request, "This app is not at the latest version! " +
                          '<a href="/upgrade"">Upgrade from GitHub</a> to receive the latest version.')


    if not config.USER_HAS_COMPLETED_CONFIGURATION:
        # If things aren't configured, redirect to the guided setup workflow
        return setup_views.setup_splash(request)
    else:
        # The default screen is the "lcd list" screen
        return lcd_test(request=request)


def add_device(request):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.add_device'):
    #     messages.error(request, 'Your account is not permissioned to add devices. Please contact an admin')
    #     return redirect("/")


    if request.POST:
        form = device_forms.DeviceForm(request.POST)
        if form.is_valid():
            # TODO - Add support for editing to this
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
            return render_with_devices(request, template_name='device_add.html', context={'form': form})
    else:
        form = device_forms.DeviceForm()
        return render_with_devices(request, template_name='device_add.html', context={'form': form})




def configure_settings(request):

    # TODO - Add user permissioning
    # if not request.user.has_perm('app.add_device'):
    #     messages.error(request, 'Your account is not permissioned to add devices. Please contact an admin')
    #     return redirect("/")


    if request.POST:
        form = device_forms.DeviceForm(request.POST)
        if form.is_valid():
            # TODO - Add support for editing to this
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
            return render(request, template_name='addtimer.html', context={'form': form, })
    else:
        form = device_forms.DeviceForm()
        return render(request, template_name='addtimer.html', context={'form': form, })


def lcd_test(request):
    # This handles generating the list of LCD screens for each device. Included are fermentation profiles so that we can
    # use them for setting temperature assignments
    from django.contrib.auth.models import User
    # Send the number of users we got in the system as a way to know if this is the first run or not.
    context={'num_users': User.objects.all().count()}
    return render_with_devices(request, template_name="device_lcd_list.html", context=context)


def device_list(request):
    return render_with_devices(request, template_name="device_list.html")


def device_config_legacy(request, device_id, control_constants):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.add_device'):
    #     messages.error(request, 'Your account is not permissioned to add devices. Please contact an admin')
    #     return redirect("/")

    active_device = BrewPiDevice.objects.get(id=device_id)

    if request.POST:
        form = device_forms.OldCCModelForm(request.POST)
        if form.is_valid():
            # Generate the new_control_constants object from the form data
            new_control_constants = form.save(commit=False)

            # At this point, we have both the OLD control constants (control_constants) and the NEW control constants
            # TODO - Modify the below to only send constants that have changed to the controller
            if not new_control_constants.save_all_to_controller(active_device):
                return render_with_devices(request, template_name='device_config_old.html',
                                           context={'form': form, 'active_device': active_device})

            # TODO - Make it so if we added a preset name we save the new preset
            # new_device.save()

            messages.success(request, 'Control constants updated for device {}'.format(active_device.device_name))
            return redirect("/")

        else:
            return render_with_devices(request, template_name='device_config_old.html',
                                       context={'form': form, 'active_device': active_device})
    else:
        form = device_forms.OldCCModelForm(instance=control_constants)
        return render_with_devices(request, template_name='device_config_old.html',
                                   context={'form': form, 'active_device': active_device})


def device_config(request, device_id):
    # TODO - Add error message if device_id is invalid
    this_device = BrewPiDevice.objects.get(id=device_id)

    control_constants, is_legacy = this_device.retrieve_control_constants()

    if control_constants is None:
        # We weren't able to retrieve the version from the controller.
        # TODO - Add error message & fix this code
        all_devices = BrewPiDevice.objects.all()
        return render(request, template_name="device_list.html", context={'all_devices': all_devices})
    elif is_legacy:
        return device_config_legacy(request, device_id, control_constants)
    else:
        # TODO - Replace this with device_config_modern or whatever it ends up getting called
        return device_config_legacy(request, device_id, control_constants)


def sensor_list(request, device_id):
    # TODO - Add error message if device_id is invalid
    active_device = BrewPiDevice.objects.get(id=device_id)

    devices_loaded = active_device.load_sensors_from_device()

    if devices_loaded:
        for this_device in active_device.available_devices:
            data = {'device_function': this_device.device_function, 'invert': this_device.invert,
                    'address': this_device.address, 'pin': this_device.pin}
            this_device.device_form = device_forms.SensorFormRevised(data)

        for this_device in active_device.installed_devices:
            data = {'device_function': this_device.device_function, 'invert': this_device.invert,
                    'address': this_device.address, 'pin': this_device.pin, 'installed': True,
                    'perform_uninstall': True}
            this_device.device_form = device_forms.SensorFormRevised(data)
    else:
        # If we weren't able to load devices, we should have set an error message instead. Display it.
        # (we can't display it directly from load_sensors_from_device() because we aren't passing request)
        messages.error(request, active_device.error_message)

    return render_with_devices(request, template_name="pin_list.html",
                               context={'available_devices': active_device.available_devices, 'active_device': active_device,
                                        'installed_devices': active_device.installed_devices, 'devices_loaded': devices_loaded})


def sensor_config(request, device_id):
    # TODO - Add error message if device_id is invalid
    active_device = BrewPiDevice.objects.get(id=device_id)

    active_device.load_sensors_from_device()

    if request.POST:
        form = device_forms.SensorFormRevised(request.POST)
        if form.is_valid():
            # OK. Here is where things get a bit tricky - We can't just rely on the form to generate the sensor object
            # as all the form really does is specify what about the sensor to change. Let's locate the sensor we need
            # to update, then adjust it based on the sensor (device) type.
            if form.data['installed']:
                sensor_to_adjust = SensorDevice.find_device_from_address_or_pin(active_device.installed_devices,
                                                                                address=form.cleaned_data['address'], pin=form.cleaned_data['pin'])
            else:
                sensor_to_adjust = SensorDevice.find_device_from_address_or_pin(active_device.available_devices,
                                                                                address=form.cleaned_data['address'], pin=form.cleaned_data['pin'])
            sensor_to_adjust.device_function = form.cleaned_data['device_function']
            sensor_to_adjust.invert = form.cleaned_data['invert']

            if sensor_to_adjust.write_config_to_controller():
                messages.success(request, 'Device definition saved for device {}'.format(device_id))
                return redirect('sensor_list', device_id=device_id)
            else:
                # TODO - Add error message if we failed to write the configuration to the controller
                return redirect('sensor_list', device_id=device_id)
        else:
            # TODO - Add error message here if the form was invalid
            return redirect('sensor_list', device_id=device_id)

    return redirect('sensor_list', device_id=device_id)


def beer_active_csv(request, device_id):
    # TODO - Add error message if device_id is invalid
    active_device = BrewPiDevice.objects.get(id=device_id)

    column_headers = BeerLogPoint.column_headers()
    if active_device.active_beer is not None:
        log_data = active_device.active_beer.beerlogpoint_set.all()
    else:
        log_data = []  # Initialize with a blank dict if we have no log data

    return render(request, template_name='csv.html', context={'csv_headers': column_headers, 'csv_data': log_data })


def device_dashboard(request, device_id):
    # TODO - Add error message if device_id is invalid
    active_device = BrewPiDevice.objects.get(id=device_id)

    return render_with_devices(request, template_name="device_dashboard.html",
                               context={'active_device': active_device,})


def find_new_mdns_brewpi_controller(request):
    services = mdnsLocator.locate_brewpi_services()

    installed_devices = []
    available_devices = []
    found_device = {}

    for this_service in services:
        found_device['mDNSname'] = services[this_service].server[:-1]
        found_device['board'] = services[this_service].properties['board']
        found_device['branch'] = services[this_service].properties['branch']
        found_device['revision'] = services[this_service].properties['revision']
        found_device['version'] = services[this_service].properties['version']

        try:
            # If we found the device, then we're golden - it's already installed (in theory)
            found_device['device'] = BrewPiDevice.objects.get(wifi_host=found_device['mDNSname'])
            installed_devices.append(found_device.copy())
        except:
            found_device['device'] = None
            available_devices.append(found_device.copy())

    return render_with_devices(request, template_name="device_mdns_locate.html",
                               context={'installed_devices': installed_devices,
                                        'available_devices': available_devices})



def device_temp_control(request, device_id):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.add_device'):
    #     messages.error(request, 'Your account is not permissioned to add devices. Please contact an admin')
    #     return redirect("/")

    try:
        active_device = BrewPiDevice.objects.get(id=device_id)
    except:
        messages.error('Unable to load device #{} for configuration'.format(device_id))
        return redirect("/")

    if request.POST:
        form = device_forms.TempControlForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['temp_control'] == 'off':
                success = active_device.set_temp_control(method=form.cleaned_data['temp_control'])
            elif form.cleaned_data['temp_control'] == 'beer_constant' or form.cleaned_data['temp_control'] == 'fridge_constant':
                success = active_device.set_temp_control(method=form.cleaned_data['temp_control'],
                                                         set_temp=float(form.cleaned_data['temperature_setting']))
            elif form.cleaned_data['temp_control'] == 'beer_profile':
                success = active_device.set_temp_control(method=form.cleaned_data['temp_control'],
                                                         profile=form.cleaned_data['profile'])
            else:
                messages.error(request, "Invalid temperature control function specified.")
                return redirect("/")

            if success:
                messages.success(request, 'Temperature control settings updated for {}'.format(active_device.device_name))
            else:
                messages.error(request, 'Unable to update temperature control settings for {}'.format(active_device.device_name))

            return redirect("/")

        else:
            messages.error(request, 'Unable to parse temperature control settings provided')
            return redirect("/")
    else:
        messages.error(request, 'No temperature control settings provided')
        return redirect("/")


def temp_panel_test(request):

    return render_with_devices(request, template_name="temp_panel_test.html",
                               context={})


def github_trigger_upgrade(request):
    commit_info = git_integration.get_local_remote_commit_info()

    if git_integration.app_is_current():
        messages.error(request, "Nothing to upgrade - Local copy and GitHub are at same commit")
    else:
        messages.success(request, "Triggered an upgrade from GitHub")
        subprocess.call("nohup utils/upgrade.sh &", shell=True)  # I think this will do it...

    return render_with_devices(request, template_name="github_trigger_upgrade.html",
                               context={'commit_info': commit_info})
