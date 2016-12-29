import datetime
from django import template
from app.models import BrewPiDevice


register = template.Library()


@register.inclusion_tag('brewpi/lcd_panel.html')
def show_lcd(this_device):
    return {'lcd_text': this_device.read_lcd(), 'this_device': this_device}


# There may be an easier way of doing this, but I want to be able to institute a pretty uniform form look across the
# site. Something complete with help text.
@register.inclusion_tag('sitewide/form_generic.html')
def form_generic(this_form_field):
    return {'form_field': this_form_field}
