from django.shortcuts import render
from django.contrib import messages
from django.shortcuts import render_to_response, redirect
from django.contrib.auth.decorators import login_required

from constance import config  # For the explicitly user-configurable stuff
from decorators import site_is_configured  # Checks if user has completed constance configuration

import beer_forms


from app.models import BrewPiDevice, Beer

def render_with_devices(request, template_name, context=None, content_type=None, status=None, using=None):
    all_devices = BrewPiDevice.objects.all()

    if context:  # Append to the context dict if it exists, otherwise create the context dict to add
        context['all_devices'] = all_devices
    else:
        context={'all_devices': all_devices}

    return render(request, template_name, context, content_type, status, using)


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

            new_beer, created = Beer.objects.get_or_create(name=form.cleaned_data['beer_name'],
                                                           device=form.cleaned_data['device'])
            if created:
                # If we just created the beer, set the temp format (otherwise, defaults to Fahrenheit)
                new_beer.format = form.cleaned_data['device'].temp_format
                new_beer.save()
                messages.success(
                    request,
                    "Successfully created beer '{}'.<br>Graph will appear when the first log points \
                    has been collected, you need to refresh the page for it to \
                    appear.".format(form.cleaned_data['beer_name']))
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
