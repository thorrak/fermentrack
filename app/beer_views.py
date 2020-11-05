from django.shortcuts import render
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

from constance import config  # For the explicitly user-configurable stuff
from .decorators import site_is_configured  # Checks if user has completed constance configuration

from . import beer_forms


from app.models import BrewPiDevice, Beer



@login_required
@site_is_configured
def beer_create(request, device_id):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.add_beer'):
    #     messages.error(request, 'Your account is not permissioned to add beers. Please contact an admin')
    #     return redirect("/")

    # This view is only intended to process data posted, generally from device_dashboard. Redirect to the dashboard
    # if we are accessed directly without post data.
    if request.POST:
        form = beer_forms.BeerCreateForm(request.POST)
        if form.is_valid():

            # TODO - Adjust this to just create the beer. Beer filenames now contain the id, and are therefore always unique
            new_beer, created = Beer.objects.get_or_create(name=form.cleaned_data['beer_name'],
                                                           device=form.cleaned_data['device'])
            if created:
                # If we just created the beer, set the temp format (otherwise, defaults to Fahrenheit)
                new_beer.format = form.cleaned_data['device'].temp_format
                new_beer.save()
                messages.success(
                    request,
                    "Successfully created beer '{}'.<br>Graph will not appear until the first log points \
                    have been collected. You will need to refresh the page for it to \
                    appear.".format(form.cleaned_data['beer_name']))

                if hasattr(new_beer.device, 'gravity_sensor'):
                    # The device this beer is being assigned to has an active gravity sensor. Lets enable logging.
                    new_beer.gravity_enabled = True
                    new_beer.save()

                    # This also means we need to start a log on the gravity sensor as well.
                    new_beer.device.gravity_sensor.create_log_and_start_logging(name=form.cleaned_data['beer_name'])
                    messages.success(request, 'Started logging gravity data for sensor {}'.format(str(new_beer.device.gravity_sensor)))

            else:
                messages.success(request, "Beer {} already exists - assigning to device".format(form.cleaned_data['beer_name']))

            if form.cleaned_data['device'].active_beer != new_beer:
                form.cleaned_data['device'].active_beer = new_beer
                form.cleaned_data['device'].save()

            form.cleaned_data['device'].start_new_brew()

        else:
            messages.error(request, "<p>Unable to create beer</p> %s" % form.errors['__all__'])

    # In all cases, redirect to device dashboard
    return redirect('device_dashboard', device_id=device_id)



@login_required
@site_is_configured
def beer_logging_status(request, device_id, logging_status):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.add_beer'):
    #     messages.error(request, 'Your account is not permissioned to add beers. Please contact an admin')
    #     return redirect("/")

    this_device = BrewPiDevice.objects.get(id=device_id)

    # logging_status is the target status. Differs a bit from how the action is referred to in brewpi.py
    if logging_status == BrewPiDevice.DATA_LOGGING_ACTIVE:
        response = this_device.manage_logging(status='resume')
        if response['status'] == 0:
            messages.success(request, "Data logging has been resumed")
        else:
            messages.error(request, response['statusMessage'])

    elif logging_status == BrewPiDevice.DATA_LOGGING_PAUSED:
        response = this_device.manage_logging(status='pause')
        if response['status'] == 0:
            messages.success(request, "Data logging has been paused")
        else:
            messages.error(request, response['statusMessage'])

    elif logging_status == BrewPiDevice.DATA_LOGGING_STOPPED:
        response = this_device.manage_logging(status='stop')
        if response['status'] == 0:
            messages.success(request, "Data logging has been stopped")
        else:
            messages.error(request, response['statusMessage'])

    else:
        messages.error(request, "Requested status is invalid!")

    # In all cases, redirect to device dashboard
    return redirect('device_dashboard', device_id=device_id)


@login_required
@site_is_configured
def beer_list(request):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.add_beer'):
    #     messages.error(request, 'Your account is not permissioned to add beers. Please contact an admin')
    #     return redirect("/")

    all_beers = Beer.objects.all().order_by('device').order_by('name')

    return render(request, template_name='beer/beer_list.html', context={'all_beers': all_beers})

@login_required
@site_is_configured
def beer_delete(request, beer_id):
    # TODO - Add user permissioning
    # if not request.user.has_perm('app.add_beer'):
    #     messages.error(request, 'Your account is not permissioned to add beers. Please contact an admin')
    #     return redirect("/")

    try:
        beer_obj = Beer.objects.get(id=beer_id)

        if beer_obj.device:
            if beer_obj.device.active_beer == beer_obj:
                # If the log is currently being logged to, we don't want to trigger a delete
                messages.error(request, u'Requested log is currently in use - Stop logging on device and reattempt')
                return redirect('beer_list')

        beer_obj.delete()
        messages.success(request, u'Beer "{}" was deleted'.format(beer_obj.name))
    except:
        messages.error(request, u'Unable to locate beer with ID {}'.format(beer_id))
    return redirect('beer_list')
