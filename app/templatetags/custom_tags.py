from django import template
from app.models import BrewPiDevice, FermentationProfile, FermentationProfilePoint
from django.utils import timezone
from app.api.clog import get_filepath_to_log
from django.conf import settings


register = template.Library()


# There may be an easier way of doing this, but I want to be able to institute a pretty uniform form look across the
# site. Something complete with help text.
@register.inclusion_tag('sitewide/form_generic.html')
def form_generic(this_form_field, replace_with_hidden=False):
    return {'form_field': this_form_field, 'replace_with_hidden': replace_with_hidden}


@register.inclusion_tag('brewpi/temp_control_modal.html')
def temp_control_modal(this_device):
    available_profiles = FermentationProfile.objects.filter(status=FermentationProfile.STATUS_ACTIVE)
    return {'temp_control_status': this_device.get_temp_control_status(), 'this_device': this_device,
            'available_profiles': available_profiles}


# This is just to make future changes a slight bit easier
@register.inclusion_tag('brewpi/temp_control_label.html')
def temp_control_label(this_device, control_status):
    return {'temp_control_status': control_status, 'this_device': this_device}

@register.filter
def durfromnow(td):
    """Take a timedelta and return now + timedelta as a date"""
    return timezone.now() + td

@register.simple_tag
def log_file_path(device_type, logfile, device_id=None):
    return get_filepath_to_log(device_type, logfile, device_id).name
