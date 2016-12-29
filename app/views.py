from django.shortcuts import render
from django.contrib import messages
from django.shortcuts import render_to_response, redirect

import device_forms

import json, time


from app.models import BrewPiDevice, OldControlConstants, NewControlConstants, PinDevice, SensorDevice, InstallSettings, BeerLogPoint

def render_with_devices(request, template_name, context=None, content_type=None, status=None, using=None):
    all_devices = BrewPiDevice.objects.all()
    site_config = InstallSettings.objects.all()
    if context:  # Append to the context dict if it exists, otherwise create the context dict to add
        context['all_devices'] = all_devices
    else:
        context={'all_devices': all_devices}
    if len(site_config)>1:  # TODO - Make this grab the first siteconfig
        context['site_config'] = site_config

    return render(request, template_name, context, content_type, status, using)


# Create your views here.
def siteroot(request):
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
                has_old_brewpi_www=form.cleaned_data['has_old_brewpi_www'],
                wwwPath=form.cleaned_data['wwwPath'],
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
                has_old_brewpi_www=form.cleaned_data['has_old_brewpi_www'],
                wwwPath=form.cleaned_data['wwwPath'],
                useInetSocket=form.cleaned_data['useInetSocket'],
                socketPort=form.cleaned_data['socketPort'],
                socketHost=form.cleaned_data['socketHost'],
                script_path=form.cleaned_data['script_path'],
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
    return render_with_devices(request, template_name="device_lcd_list.html")


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
            if not new_control_constants.save_all_to_controller():
                return render_with_devices(request, template_name='device_config_old.html',
                                           context={'form': form, 'active_device': active_device})

            # TODO - Make it so if we added a preset name we save the new preset
            # new_device.save()

            messages.success(request, 'Control constants updated for device {}'.format(device_id))
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

    active_device.load_sensors_from_device()

    # TODO - Add error handling here -- If we can't reach brewpi-script, we can't read available devices, etc.
    for this_device in active_device.available_devices:
        data = {'device_function': this_device.device_function, 'invert': this_device.invert,
                'address': this_device.address, 'pin': this_device.pin}
        this_device.device_form = device_forms.SensorFormRevised(data)

    for this_device in active_device.installed_devices:
        data = {'device_function': this_device.device_function, 'invert': this_device.invert,
                'address': this_device.address, 'pin': this_device.pin, 'installed': True,
                'perform_uninstall': True}
        this_device.device_form = device_forms.SensorFormRevised(data)

    return render_with_devices(request, template_name="pin_list.html",
                               context={'available_devices': active_device.available_devices, 'active_device': active_device,
                                        'installed_devices': active_device.installed_devices})


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
    log_data = active_device.active_beer.beerlogpoint_set.all()

    return render(request, template_name='csv.html', context={'csv_headers': column_headers, 'csv_data': log_data })


def device_dashboard(request, device_id):
    # TODO - Add error message if device_id is invalid
    active_device = BrewPiDevice.objects.get(id=device_id)

    return render_with_devices(request, template_name="device_dashboard.html",
                               context={'active_device': active_device,})


def profile_new(request, device_id=None):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.add_fermentation_profile'):
    #     messages.error(request, 'Your account is not permissioned to add fermentation profiles. Please contact an admin')
    #     return redirect("/")

    if device_id is not None:
        active_device = BrewPiDevice.objects.get(id=device_id)
    else:
        active_device = None

    if request.POST:
        form = device_forms.FermentationProfileForm(request.POST)
        if form.is_valid():
            # Generate the new_control_constants object from the form data
            new_fermentation_profile = form.save()
            messages.success(request, 'New fermentation profile created')
            return redirect("/")  # TODO - Change this to redirect to the fermentation profile view screen

        else:
            return render_with_devices(request, template_name='profile_new.html',
                                       context={'form': form, 'active_device': active_device})
    else:
        form = device_forms.FermentationProfileForm()
        return render_with_devices(request, template_name='profile_new.html',
                                   context={'form': form, 'active_device': active_device})
