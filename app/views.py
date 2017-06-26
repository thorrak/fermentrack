from django.shortcuts import render
from django.contrib import messages
from django.shortcuts import render_to_response, redirect
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone

from constance import config  # For the explicitly user-configurable stuff
from decorators import site_is_configured, login_if_required_for_dashboard

import device_forms, profile_forms, beer_forms, setup_forms
import setup_views

import mdnsLocator

import almost_json
from django.http import HttpResponse

import json, datetime, pytz, os, random

import git_integration
import subprocess

import connection_debug, udev_integration

import fermentrack_django.settings as settings


from app.models import BrewPiDevice, OldControlConstants, NewControlConstants, PinDevice, SensorDevice, BeerLogPoint, FermentationProfile, Beer
from django.contrib.auth.models import User


def render_with_devices(request, template_name, context=None, content_type=None, status=None, using=None):
    all_devices = BrewPiDevice.objects.all()

    if context:  # Append to the context dict if it exists, otherwise create the context dict to add
        context['all_devices'] = all_devices
    else:
        context={'all_devices': all_devices}

    return render(request, template_name, context, content_type, status, using)


# Siteroot is a lazy way of determining where to direct the user when they go to http://devicename.local/
def siteroot(request):

    # In addition to requiring the site to be configured, we require that there be a user account. Due to the
    # setup workflow, the user will generally be created before constance configuration takes place, but if
    # the user account gets deleted (for example, in the admin) we want the user to go through that portion
    # of account setup.
    num_users=User.objects.all().count()

    if config.GIT_UPDATE_TYPE != "none":
        # TODO - Reset this to 18 hours
        # Check the git status at least every 6 hours
        now_time = timezone.now()
        if config.LAST_GIT_CHECK < now_time - datetime.timedelta(hours=6):
            try:
                if git_integration.app_is_current():
                    config.LAST_GIT_CHECK = now_time
                else:
                    messages.info(request, "This app is not at the latest version! " +
                                  '<a href="/upgrade"">Upgrade from GitHub</a> to receive the latest version.')
            except:
                # If we can't check for the latest version info, skip and move on
                pass


    if not config.USER_HAS_COMPLETED_CONFIGURATION or num_users <= 0:
        # If things aren't configured, redirect to the guided setup workflow
        return redirect('setup_splash')
    else:
        # The default screen is the "lcd list" screen
        return device_lcd_list(request=request)


@login_required
@site_is_configured  # Checks if the user completed constance configuration
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
                prefer_connecting_via_udev=form.cleaned_data['prefer_connecting_via_udev'],
            )

            new_device.save()

            # Once the device is added, go ahead and autodetect the udev serial number (if we're connecting via serial)
            if new_device.connection_type == BrewPiDevice.CONNECTION_SERIAL:
                new_device.set_udev_from_port()

            messages.success(request, u'Device {} Added.<br>Please wait a few seconds for controller to start'.format(new_device))
            return redirect("/")

        else:
            return render_with_devices(request, template_name='setup/device_add.html', context={'form': form})
    else:
        # We don't want two devices to have the same port, and the port number doesn't really matter. Just
        # randomize it.
        random_port = random.randint(2000,3000)
        initial_values = {'socketPort': random_port, 'temp_format': config.TEMPERATURE_FORMAT}

        form = device_forms.DeviceForm(initial=initial_values)
        return render_with_devices(request, template_name='setup/device_add.html', context={'form': form})


@site_is_configured
@login_if_required_for_dashboard
def device_lcd_list(request):
    # This handles generating the list of LCD screens for each device.
    # Loading the actual data for the LCD screens is handled by Vue.js which loads the data via calls to api/lcd.py
    return render_with_devices(request, template_name="device_lcd_list.html")


@login_required
@site_is_configured
def device_control_constants_legacy(request, device_id, control_constants):
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
                return render_with_devices(request, template_name='device_control_constants_old.html',
                                           context={'form': form, 'active_device': active_device})

            # TODO - Make it so if we added a preset name we save the new preset
            # new_device.save()

            messages.success(request, u'Control constants updated for device {}'.format(active_device))
            return redirect("/")

        else:
            return render_with_devices(request, template_name='device_control_constants_old.html',
                                       context={'form': form, 'active_device': active_device})
    else:
        form = device_forms.OldCCModelForm(instance=control_constants)
        return render_with_devices(request, template_name='device_control_constants_old.html',
                                   context={'form': form, 'active_device': active_device})


@login_required
@site_is_configured
def device_control_constants(request, device_id):
    try:
        active_device = BrewPiDevice.objects.get(id=device_id)
    except:
        messages.error(request, "Unable to load device with ID {}".format(device_id))
        return redirect('siteroot')

    control_constants, is_legacy = active_device.retrieve_control_constants()

    if control_constants is None:
        # We weren't able to retrieve the version from the controller.
        messages.error(request, u"Unable to reach brewpi-script for device {}".format(active_device))
        return redirect('device_dashboard', device_id=device_id)

    elif is_legacy:
        return device_control_constants_legacy(request, device_id, control_constants)
    else:
        # TODO - Replace this with device_control_constants_modern or whatever it ends up getting called
        return device_control_constants_legacy(request, device_id, control_constants)


@login_required
@site_is_configured
def sensor_list(request, device_id):
    try:
        active_device = BrewPiDevice.objects.get(id=device_id)
    except:
        messages.error(request, "Unable to load device with ID {}".format(device_id))
        return redirect('siteroot')

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


@login_required
@site_is_configured
def sensor_config(request, device_id):
    try:
        active_device = BrewPiDevice.objects.get(id=device_id)
    except:
        messages.error(request, "Unable to load device with ID {}".format(device_id))
        return redirect('siteroot')

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
                # We failed to write the configuration to the controller. Show an error.
                messages.error(request, "Failed to write the configuration to the controller.")
                return redirect('sensor_list', device_id=device_id)
        else:
            messages.error(request, "There was an error processing the form. Please review and resubmit.")
            return redirect('sensor_list', device_id=device_id)

    return redirect('sensor_list', device_id=device_id)


@site_is_configured
@login_if_required_for_dashboard
def device_dashboard(request, device_id, beer_id=None):
    try:
        active_device = BrewPiDevice.objects.get(id=device_id)
    except:
        messages.error(request, "Unable to load device with ID {}".format(device_id))
        return redirect('siteroot')
    beer_create_form = beer_forms.BeerCreateForm()

    if beer_id is None:
        beer_obj = active_device.active_beer or None
        available_beer_logs = Beer.objects.filter(device_id=active_device.id)  # Do I want to exclude the active beer?
    else:
        beer_obj = Beer.objects.get(id=beer_id, device_id=active_device.id) or None
        available_beer_logs = Beer.objects.filter(device_id=active_device.id).exclude(id=beer_id)

    if beer_obj is None:
        # TODO - Determine if we want to load some fake "example" data (similar to what brewpi-www does)
        beer_file_url = "/data/fake.csv"
    else:
        beer_file_url = beer_obj.data_file_url('base_csv')


    return render_with_devices(request, template_name="device_dashboard.html",
                               context={'active_device': active_device, 'beer_create_form': beer_create_form,
                                        'beer': beer_obj, 'temp_display_format': config.DATE_TIME_FORMAT_DISPLAY,
                                        'column_headers': Beer.column_headers_to_graph_string('base_csv'),
                                        'beer_file_url': beer_file_url, 'available_beer_logs': available_beer_logs,
                                        'selected_beer_id': beer_id})


@login_required
@site_is_configured
def device_temp_control(request, device_id):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.add_device'):
    #     messages.error(request, 'Your account is not permissioned to add devices. Please contact an admin')
    #     return redirect("/")

    try:
        active_device = BrewPiDevice.objects.get(id=device_id)
    except:
        messages.error(request, "Unable to load device with ID {}".format(device_id))
        return redirect('siteroot')

    if request.POST:
        form = device_forms.TempControlForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['temp_control'] == 'off':
                success = active_device.set_temp_control(method=form.cleaned_data['temp_control'])
            elif form.cleaned_data['temp_control'] == 'beer_constant' or form.cleaned_data['temp_control'] == 'fridge_constant':
                try:
                    success = active_device.set_temp_control(method=form.cleaned_data['temp_control'],
                                                             set_temp=float(form.cleaned_data['temperature_setting']))
                except:
                    success = False
            elif form.cleaned_data['temp_control'] == 'beer_profile':
                if 'start_at' in form.cleaned_data:
                    start_at = form.cleaned_data['start_at']
                else:
                    start_at = None

                success = active_device.set_temp_control(method=form.cleaned_data['temp_control'],
                                                         profile=form.cleaned_data['profile'], profile_startat=start_at)
            else:
                messages.error(request, "Invalid temperature control function specified.")
                return redirect('siteroot')

            if success:
                messages.success(request, u'Temperature control settings updated for {}. Please wait a few seconds for settings to take effect.'.format(active_device))
                if active_device.active_beer is None:
                    # We started temperature control, but aren't logging anything. Prompt the user.
                    messages.info(request, 'Temperature control enabled, but logging is off. Start a new beer from the device dashboard.')
                elif active_device.logging_status != active_device.DATA_LOGGING_ACTIVE:
                    # We altered temperature control, but logging is paused. Prompt the user.
                    messages.info(request, 'Temperature control enabled, but logging is off. Start a new beer from the device dashboard.')
            else:
                messages.error(request, u'Unable to update temperature control settings for {}'.format(active_device))

            return redirect('siteroot')

        else:
            messages.error(request, 'Unable to parse temperature control settings provided')
            return redirect('siteroot')
    else:
        messages.error(request, 'No temperature control settings provided')
        return redirect('siteroot')


@login_required
@site_is_configured
def github_trigger_upgrade(request):
    # TODO - Add permission check here
    commit_info = git_integration.get_local_remote_commit_info()

    allow_git_branch_switching = config.ALLOW_GIT_BRANCH_SWITCHING
    app_is_current = git_integration.app_is_current()
    git_update_type = config.GIT_UPDATE_TYPE

    tags = git_integration.get_tag_info()

    if allow_git_branch_switching:
        branch_info = git_integration.get_remote_branch_info()
    else:
        branch_info = {}

    if request.POST:
        if app_is_current and 'new_branch' not in request.POST and 'tag' not in request.POST:
            messages.error(request, "Nothing to upgrade - Local copy and GitHub are at same commit")
        else:
            messages.success(request, "Triggered an upgrade from GitHub")

            if 'tag' in request.POST:
                # If we were passed a tag name, explicitly update to it. Assume (for now) all tags are within master
                cmd = "nohup utils/upgrade.sh -t \"{}\" -b \"master\" &".format(request.POST['tag'])
            elif not allow_git_branch_switching or 'new_branch' not in request.POST:
                # We'll use the branch name from the current commit if we either aren't allowed to directly switch branches
                # or haven't been passed a branch name
                cmd = "nohup utils/upgrade.sh -b \"{}\" &".format(commit_info['local_branch'])
            else:
                cmd = "nohup utils/upgrade.sh -b \"{}\" &".format(request.POST['new_branch'])
            subprocess.call(cmd, shell=True)

    else:
        # We'll display this error message if the page is being accessed and no form has been posted
        if app_is_current:
            messages.warning(request, "Nothing to upgrade - Local copy and GitHub are at same commit")

    return render_with_devices(request, template_name="github_trigger_upgrade.html",
                               context={'commit_info': commit_info, 'app_is_current': app_is_current,
                                        'branch_info': branch_info, 'tags': tags, 'git_update_type': git_update_type,
                                        'allow_git_branch_switching': allow_git_branch_switching})


def login(request, next=None):
    if not next:
        if 'next' in request.GET:
            next=request.GET['next']
        elif 'next' in request.POST:
            next=request.POST['next']
        else:
            next="/"

    if 'username' in request.POST:
        target_user = auth.authenticate(username=request.POST['username'], password=request.POST['password'])

        if target_user:  # If the user authenticated, process login & redirect
            auth.login(request, target_user)

            messages.success(request, "Logged in")

            if 'next' in request.POST:
                if len(request.POST['next']) > 1:
                    return redirect(request.POST['next'])

            return redirect('siteroot')

        else:
            messages.error(request, "Login failed")
            return render(request, template_name="site_login.html", context={'pagetitle': 'Log In', 'next': next})

    # If we hit this, we just need to display the form (no valid form input received)
    return render(request, template_name="site_login.html", context={'pagetitle': 'Log In', 'next': next})


def logout(request):
    if request.user.is_authenticated():
        auth.logout(request)
        return redirect('siteroot')
    else:
        return redirect('login')

@login_required
@site_is_configured
def site_settings(request):
    # TODO - Add user permissioning. The wizard creates the user and login so we can check for superuser here


    if not config.USER_HAS_COMPLETED_CONFIGURATION:
        return redirect('siteroot')

    if request.POST:
        form = setup_forms.GuidedSetupConfigForm(request.POST)
        if form.is_valid():
            f = form.cleaned_data
            config.BREWERY_NAME = f['brewery_name']
            config.DATE_TIME_FORMAT_DISPLAY = f['date_time_format_display']
            config.REQUIRE_LOGIN_FOR_DASHBOARD = f['require_login_for_dashboard']
            config.TEMPERATURE_FORMAT = f['temperature_format']
            config.PREFERRED_TIMEZONE = f['preferred_timezone']
            config.USER_HAS_COMPLETED_CONFIGURATION = True  # Toggle once they've completed the configuration workflow
            messages.success(request, 'App configuration has been saved')
            return redirect('siteroot')
        else:
            return render_with_devices(request, template_name='site_config.html',
                                       context={'form': form,
                                                'completed_config': config.USER_HAS_COMPLETED_CONFIGURATION})
    else:
        form = setup_forms.GuidedSetupConfigForm()
        return render_with_devices(request, template_name='site_config.html',
                                   context={'form': form,
                                            'completed_config': config.USER_HAS_COMPLETED_CONFIGURATION})




@login_required
@site_is_configured
def device_control_constants_legacy(request, device_id, control_constants):
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
                return render_with_devices(request, template_name='device_control_constants_old.html',
                                           context={'form': form, 'active_device': active_device})

            # TODO - Make it so if we added a preset name we save the new preset
            # new_device.save()

            messages.success(request, u'Control constants updated for device {}'.format(active_device))
            return redirect("/")

        else:
            return render_with_devices(request, template_name='device_control_constants_old.html',
                                       context={'form': form, 'active_device': active_device})
    else:
        form = device_forms.OldCCModelForm(instance=control_constants)
        return render_with_devices(request, template_name='device_control_constants_old.html',
                                   context={'form': form, 'active_device': active_device})


@login_required
@site_is_configured
def device_eeprom_reset(request, device_id):
    try:
        active_device = BrewPiDevice.objects.get(id=device_id)
    except:
        messages.error(request, "Unable to load device with ID {}".format(device_id))
        return redirect('siteroot')

    # This may be unncecessary for the EEPROM reset process, but using it as a proxy to check if we can connect
    control_constants, is_legacy = active_device.retrieve_control_constants()

    if control_constants is None:
        # We weren't able to retrieve the version from the controller.
        messages.error(request, u"Unable to reach brewpi-script for device {}".format(active_device))
        return redirect('device_dashboard', device_id=device_id)
    else:
        active_device.reset_eeprom()
        messages.success(request, "Device EEPROM reset")
        return redirect("device_control_constants", device_id=device_id)

def site_help(request):
    return render_with_devices(request, template_name='site_help.html', context={})


@login_required
@site_is_configured
def device_manage(request, device_id):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.edit_device'):
    #     messages.error(request, 'Your account is not permissioned to edit devices. Please contact an admin')
    #     return redirect("/")

    try:
        active_device = BrewPiDevice.objects.get(id=device_id)
    except:
        messages.error(request, "Unable to load device with ID {}".format(device_id))
        return redirect('siteroot')

    # Forms posted back to device_manage are explicitly settings update forms
    if request.POST:
        form = device_forms.DeviceForm(request.POST)

        if form.is_valid():
            # Update the device settings based on what we were passed via the form
            active_device.device_name=form.cleaned_data['device_name']
            active_device.temp_format=form.cleaned_data['temp_format']
            active_device.data_point_log_interval=form.cleaned_data['data_point_log_interval']
            active_device.useInetSocket=form.cleaned_data['useInetSocket']
            active_device.socketPort=form.cleaned_data['socketPort']
            active_device.socketHost=form.cleaned_data['socketHost']
            active_device.serial_port=form.cleaned_data['serial_port']
            active_device.serial_alt_port=form.cleaned_data['serial_alt_port']
            # Not going to allow editing the board type. Can revisit if there seems to be a need later
            # active_device.board_type=form.cleaned_data['board_type']
            active_device.socket_name=form.cleaned_data['socket_name']
            active_device.connection_type=form.cleaned_data['connection_type']
            active_device.wifi_host=form.cleaned_data['wifi_host']
            active_device.wifi_port=form.cleaned_data['wifi_port']

            active_device.save()

            messages.success(request, u'Device {} Updated.<br>Please wait a few seconds for the connection to restart'.format(active_device))

            active_device.restart_process()

            return render_with_devices(request, template_name='device_manage.html',
                                       context={'form': form, 'active_device': active_device})

        else:
            return render_with_devices(request, template_name='device_manage.html',
                                       context={'form': form, 'active_device': active_device})
    else:
        # This would probably be easier if I was to use ModelForm instead of Form, but at this point I don't feel like
        # refactoring it. Project for later if need be.
        initial_values = {
            'device_name': active_device.device_name,
            'temp_format': active_device.temp_format,
            'data_point_log_interval': active_device.data_point_log_interval,
            'connection_type': active_device.connection_type,
            'useInetSocket': active_device.useInetSocket,
            'socketPort': active_device.socketPort,
            'socketHost': active_device.socketHost,
            'serial_port': active_device.serial_port,
            'serial_alt_port': active_device.serial_alt_port,
            'board_type': active_device.board_type,
            'socket_name': active_device.socket_name,
            'wifi_host': active_device.wifi_host,
            'wifi_port': active_device.wifi_port,
        }

        form = device_forms.DeviceForm(initial=initial_values)
        return render_with_devices(request, template_name='device_manage.html',
                                   context={'form': form, 'active_device': active_device})

def device_uninstall(request, device_id):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.delete_device'):
    #     messages.error(request, 'Your account is not permissioned to uninstall devices. Please contact an admin')
    #     return redirect("/")

    try:
        active_device = BrewPiDevice.objects.get(id=device_id)
    except:
        messages.error(request, "Unable to load device with ID {}".format(device_id))
        return redirect('siteroot')

    if request.POST:
        if 'remove_1' in request.POST and 'remove_2' in request.POST and 'remove_3' in request.POST:
            if request.POST['remove_1'] == "on" and request.POST['remove_2'] == "on" and request.POST['remove_3'] == "on":
                # messages.success(request, "The device '" + unicode(active_device) + "' was successfully uninstalled.")
                messages.success(request, u"The device '{}' was successfully uninstalled.".format(active_device))
                active_device.delete()
                # TODO - Trigger Circus to reload properly, rather than using an external script
                # As stone noted - this isn't needed as Circus will autodetect if a controller was removed and kill
                # the instance of brewpi-script associated with it. This isn't necessary as a result.
                # cmd = "nohup utils/reset_circus.sh &"
                # subprocess.call(cmd, shell=True)
                return redirect("siteroot")

        # If we get here, one of the switches wasn't toggled
        messages.error(request, "All three switches must be set to 'yes' to uninstall a device.")
        return redirect("device_manage", device_id=device_id)
    else:
        messages.error(request, "To uninstall a device, use the form on the 'Manage Device' page.")
        return redirect("device_manage", device_id=device_id)


# So here's the deal -- If we want to write json files sequentially, we have to skip closing the array. If we want to
# then interpret them using JavaScript, however, we MUST have fully formed, valid json. To acheive that, we're going to
# wrap the json file and append the closing bracket after dumping its contents to the browser.
def almost_json_view(request, device_id, beer_id):
    json_close = "\r\n]"

    beer_obj = Beer.objects.get(id=beer_id, device_id=device_id)

    filename = os.path.join(settings.BASE_DIR, settings.DATA_ROOT, beer_obj.full_filename("annotation_json"))

    if os.path.isfile(filename):  # If there are no annotations, return an empty
        wrapper = almost_json.AlmostJsonWrapper(file(filename), closing_string=json_close)
        response = HttpResponse(wrapper, content_type="application/json")
        response['Content-Length'] = os.path.getsize(filename) + len(json_close)
        return response
    else:
        empty_array = []
        return JsonResponse(empty_array, safe=False, json_dumps_params={'indent': 4})


def debug_connection(request, device_id):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.delete_device'):
    #     messages.error(request, 'Your account is not permissioned to uninstall devices. Please contact an admin')
    #     return redirect("/")

    try:
        active_device = BrewPiDevice.objects.get(id=device_id)
    except:
        messages.error(request, "Unable to load device with ID {}".format(device_id))
        return redirect('siteroot')

    tests=[]
    FAILED = 'Failed'
    PASSED = 'Passed'


    if active_device.status != BrewPiDevice.STATUS_ACTIVE:
        test_result = {'name': 'Device Status Test', 'parameter': active_device.status, 'status': FAILED,
                       'result': 'Device not active'}
    else:
        test_result = {'name': 'Device Status Test', 'parameter': active_device.status, 'status': PASSED,
                       'result': 'Device active & managed by Circus'}
    tests.append(test_result)



    if active_device.connection_type == BrewPiDevice.CONNECTION_WIFI:
        # For WiFi, the first thing we check is if we can resolve the mDNS hostname
        mdns_lookup = connection_debug.dns_lookup(active_device.wifi_host)

        if mdns_lookup is None:
            test_result = {'name': 'DNS Lookup Test', 'parameter': active_device.wifi_host, 'status': FAILED,
                           'result': 'No DNS response'}
        else:
            test_result = {'name': 'DNS Lookup Test', 'parameter': active_device.wifi_host, 'status': PASSED,
                           'result': mdns_lookup}
        tests.append(test_result)


        # Once that's done, we'll test connecting to the mDNS hostname & cached IP address
        # Start with the mDNS hostname (if mdns_lookup was successful)
        if mdns_lookup is not None:
            hostname = active_device.wifi_host
            connection_check, version_check, version_string = connection_debug.test_telnet(hostname)

            if connection_check:
                # We were able to telnet into the hostname
                test_result = {'name': 'Connection Test', 'parameter': hostname, 'status': PASSED,
                               'result': 'Connected'}
                tests.append(test_result)

                if version_check:
                    # We were able to get a version number from the host - this is a complete success
                    test_result = {'name': 'Controller Response Test', 'parameter': hostname, 'status': PASSED,
                                   'result': version_string}
                    tests.append(test_result)
                else:
                    # We weren't able to get a version number from the host
                    test_result = {'name': 'Controller Response Test', 'parameter': hostname, 'status': FAILED,
                                   'result': ''}
                    tests.append(test_result)
            else:
                test_result = {'name': 'Connection Test', 'parameter': hostname, 'status': FAILED,
                               'result': 'Unable to connect'}
                tests.append(test_result)

        if len(active_device.wifi_host_ip) > 7:
            hostname = active_device.wifi_host_ip
            connection_check, version_check, version_string = connection_debug.test_telnet(hostname)

            test_result = {'name': 'Cached IP Test', 'parameter': hostname, 'status': PASSED,
                           'result': 'Available'}
            tests.append(test_result)

            if connection_check:
                # We were able to telnet into the hostname
                test_result = {'name': 'Connection Test', 'parameter': hostname, 'status': PASSED,
                               'result': 'Connected'}
                tests.append(test_result)

                if version_check:
                    # We were able to get a version number from the host - this is a complete success
                    test_result = {'name': 'Controller Response Test', 'parameter': hostname, 'status': PASSED,
                                   'result': version_string}
                    tests.append(test_result)
                else:
                    # We weren't able to get a version number from the host
                    test_result = {'name': 'Controller Response Test', 'parameter': hostname, 'status': FAILED,
                                   'result': ''}
                    tests.append(test_result)
            else:
                test_result = {'name': 'Connection Test', 'parameter': hostname, 'status': FAILED,
                               'result': 'Unable to connect'}
                tests.append(test_result)
        else:
            test_result = {'name': 'Cached IP Test', 'parameter': active_device.wifi_host_ip, 'status': FAILED,
                           'result': 'Unavailable'}
            tests.append(test_result)

    elif active_device.connection_type == BrewPiDevice.CONNECTION_SERIAL:
        if udev_integration.valid_platform_for_udev():
            # Pyudev is available on this platform - let's see if we have a USB serial number set
            test_result = {'name': 'Udev Availability Test', 'parameter': udev_integration.get_platform(), 'status': PASSED,
                           'result': 'pyudev is available & loaded'}
            tests.append(test_result)

            if active_device.prefer_connecting_via_udev:
                # Let the user know they are using udev if available
                test_result = {'name': 'USB Serial Number (SN) Usage Test', 'parameter': active_device.prefer_connecting_via_udev, 'status': PASSED,
                               'result': 'Will look up port via USB serial number'}
                tests.append(test_result)

            else:
                # Let the user know they AREN'T using udev (and it's available)
                test_result = {'name': 'USB SN Usage Test', 'parameter': active_device.prefer_connecting_via_udev, 'status': FAILED,
                               'result': 'Will NOT look up port via USB serial number'}
                tests.append(test_result)

            if len(active_device.udev_serial_number) > 1:
                # The user has a seemingly valid USB serial number set on the device
                test_result = {'name': 'USB SN Test', 'parameter': '', 'status': PASSED,
                               'result': active_device.udev_serial_number}
                tests.append(test_result)

                if active_device.prefer_connecting_via_udev:
                    # If the user has everything set up to use udev (and actually wants to use it) then check what
                    # we find if we look up the USB serial number
                    found_node = udev_integration.get_node_from_serial(active_device.udev_serial_number)

                    if found_node is None:
                        # We weren't able to find a matching USB device with that serial number
                        test_result = {'name': 'USB SN Availability Test', 'parameter': '(USB SN)', 'status': FAILED,
                                       'result': 'No device with that serial number found'}
                        tests.append(test_result)
                    else:
                        # We found a device that matched that serial number
                        test_result = {'name': 'USB SN Availability Test', 'parameter': '(USB SN)', 'status': PASSED,
                                       'result': found_node}
                        tests.append(test_result)

                        # Last test - Check if the serial port matches what we just found via the USB lookup
                        if found_node == active_device.serial_port:
                            # It matched!
                            test_result = {'name': 'Udev Matches Cached Port Test', 'parameter': found_node,
                                           'status': PASSED, 'result': active_device.serial_port}
                            tests.append(test_result)
                        else:
                            # It... didn't match.
                            test_result = {'name': 'Udev Matches Cached Port Test', 'parameter': found_node,
                                           'status': FAILED, 'result': active_device.serial_port}
                            tests.append(test_result)

            else:
                # There isn't a seemingly valid USB serial number set on the device
                test_result = {'name': 'USB Serial Number Test', 'parameter': '', 'status': FAILED,
                               'result': active_device.udev_serial_number}
                tests.append(test_result)

        else:
            # Pyudev isn't available on this platform
            test_result = {'name': 'Udev Availability Test', 'parameter': udev_integration.get_platform(), 'status': FAILED,
                           'result': 'pyudev is not available, or isn\'t loaded'}
            tests.append(test_result)


    return render_with_devices(request, template_name='device_debug_connection.html',
                               context={'tests': tests, 'active_device': active_device})



