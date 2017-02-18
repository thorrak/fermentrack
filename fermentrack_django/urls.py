from django.conf.urls import url
from django.contrib import admin

from django.conf import settings
from django.conf.urls.static import static

import app.views
import app.profile_views
import app.setup_views
import app.beer_views
import app.api.lcd

admin.autodiscover()

# In addition to urlpatterns below, three paths are mapped by the nginx config file:
# r'^static/' - Maps to collected_static/. Contains collected static files.
# r'^media/' - Maps to media/. Contains uploaded files. Currently unused.
# r'^data/' - Maps to data/. Contains data points collected by brewpi.py.

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^lcd_test/$', app.views.lcd_test, name='lcd_test'),
    url(r'^$', app.views.siteroot, name='siteroot'),

    url(r'^upgrade/$', app.views.github_trigger_upgrade, name='github_trigger_upgrade'),

    ### Device Views
    url(r'^devices/$', app.views.device_list, name='device_list'),
    url(r'^devices/add/$', app.views.add_device, name='device_add'),

    ## New install Guided Setup Views
    url(r'setup/$', app.setup_views.setup_splash, name="setup_splash"),
    url(r'setup/add_user/$', app.setup_views.setup_add_user, name="setup_add_user"),
    url(r'setup/settings/$', app.setup_views.setup_config, name="setup_config"),

    ## Device Guided Setup Views
    url(r'^devices/guided/$', app.setup_views.device_guided_select_device, name='device_guided_select_device'),
    url(r'^devices/guided/(?P<device_family>[A-Za-z0-9]{1,20})/flash_prompt/$', app.setup_views.device_guided_flash_prompt, name='device_guided_flash_prompt'),
    url(r'^devices/guided/(?P<device_family>[A-Za-z0-9]{1,20})/flash/$', app.setup_views.device_guided_flash_prompt, name='device_guided_flash_prompt'),
    url(r'^devices/guided/(?P<device_family>[A-Za-z0-9]{1,20})/connection/$', app.setup_views.device_guided_serial_wifi, name='device_guided_serial_wifi'),
    url(r'^devices/guided/mdns/$', app.setup_views.device_guided_find_mdns, name='device_guided_mdns'),
    url(r'^devices/guided/mdns/(?P<mdns_id>[A-Za-z0-9.]{1,60})/$', app.setup_views.device_guided_add_mdns, name='device_guided_add_mdns'),

    ## Other main device views
    url(r'^devices/(?P<device_id>\d{1,20})/config/$', app.views.device_config, name='device_config'),
    url(r'^devices/(?P<device_id>\d{1,20})/dashboard/$', app.views.device_dashboard, name='device_dashboard'),
    # TODO - Implement backlight toggle AJAX API call
    url(r'^devices/(?P<device_id>\d{1,20})/backlight/toggle/$', app.views.device_dashboard, name='device_toggle_backlight'),
    # TODO - Implement temperature control AJAX API calls
    url(r'^devices/(?P<device_id>\d{1,20})/temp_control/$', app.views.device_temp_control, name='device_temp_control'),

    # Device Utility & Internal Views
    url(r'^devices/(?P<device_id>\d{1,20})/beer/csv/active_beer.csv$', app.views.beer_active_csv, name='csv_active_beer'),
    url(r'^devices/(?P<device_id>\d{1,20})/beer/create/$', app.beer_views.beer_create, name='beer_create'),
    url(r'^devices/(?P<device_id>\d{1,20})/beer/status/(?P<logging_status>[A-Za-z0-9]{1,20})/$', app.beer_views.beer_logging_status, name='beer_logging_status'),
    # url(r'^devices/(\d{1,20})/beer/csv/(\d{1,20}).csv$', app.views.device_config, name='csv_numbered'),

    url(r'^devices/(?P<device_id>\d{1,20})/sensors/$', app.views.sensor_list, name='sensor_list'),
    url(r'^devices/(?P<device_id>\d{1,20})/sensors/config/$', app.views.sensor_config, name='sensor_config'),

    # Fermentation Profile Views
    url(r'^fermentation_profile/list/$', app.profile_views.profile_list, name='profile_list'),
    url(r'^fermentation_profile/new/$', app.profile_views.profile_new, name='profile_new'),
    url(r'^fermentation_profile/(?P<profile_id>\d{1,20})/$', app.profile_views.profile_new, name='profile_view'),
    url(r'^fermentation_profile/(?P<profile_id>\d{1,20})/edit/$', app.profile_views.profile_edit, name='profile_edit'),
    url(r'^fermentation_profile/(?P<profile_id>\d{1,20})/delete/$', app.profile_views.profile_delete, name='profile_delete'),
    url(r'^fermentation_profile/(?P<profile_id>\d{1,20})/undelete/$', app.profile_views.profile_undelete, name='profile_undelete'),
    url(r'^fermentation_profile/(?P<profile_id>\d{1,20})/point/(?P<point_id>\d{1,20})/delete$', app.profile_views.profile_setpoint_delete, name='profile_setpoint_delete'),

    # Api Views
    url(r'^api/lcd/(?P<device_name>\w+)$', app.api.lcd.getLCD, name="getLCD"),
    url(r'^api/lcd/$', app.api.lcd.getLCDs, name="getLCDs"),

    url(r'^panel_test/$', app.views.temp_panel_test, name='temp_panel_test'),

    # Login/Logout Views
    url(r'^accounts/login/$', app.views.login, name='login'),
    url(r'^accounts/logout/$', app.views.logout, name='logout'),

    # Site-specific views (Help, Settings, etc.)
    url(r'site/settings/$', app.views.site_settings, name="site_settings"),
    url(r'site/help/$', app.setup_views.setup_config, name="site_help"),

] + static(settings.DATA_URL, document_root=settings.DATA_ROOT)  # To enable viewing data files during development
