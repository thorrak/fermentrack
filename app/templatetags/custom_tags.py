import datetime
from django import template
from app.models import BrewPiDevice, FermentationProfile, FermentationProfilePoint


register = template.Library()

# TODO - Delete this if it is no longer used in active code (
@register.inclusion_tag('brewpi/lcd_panel.html')
def show_lcd(this_device):
    return {'lcd_text': this_device.read_lcd(), 'this_device': this_device}


# There may be an easier way of doing this, but I want to be able to institute a pretty uniform form look across the
# site. Something complete with help text.
@register.inclusion_tag('sitewide/form_generic.html')
def form_generic(this_form_field):
    return {'form_field': this_form_field}


@register.inclusion_tag('brewpi/temp_control_modal.html')
def temp_control_modal(this_device):
    available_profiles = FermentationProfile.objects.filter(status=FermentationProfile.STATUS_ACTIVE)
    return {'temp_control_status': this_device.get_temp_control_status(), 'this_device': this_device,
            'available_profiles': available_profiles}


# This is just to make future changes a slight bit easier
@register.inclusion_tag('brewpi/temp_control_label.html')
def temp_control_label(this_device, control_status):
    return {'temp_control_status': control_status, 'this_device': this_device}


@register.inclusion_tag('brewpi/temp_panel.html')
def temp_panel(device_name, fridge_temp, target_temp):
    device_status = {}
    device_status['fridge_temp'] = fridge_temp
    device_status['fridge_temp_units'] = 'F'

    device_status['target_temp'] = target_temp
    device_status['target_temp_units'] = 'F'
    device_status['target_temp_mode'] = 'Fridge Constant'

    device_status['device_name'] = device_name

    return {'device_status': device_status}
