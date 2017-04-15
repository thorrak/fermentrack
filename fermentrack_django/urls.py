from django.conf.urls import url
from django.contrib import admin

from django.conf import settings
from django.conf.urls.static import static

import app.views
import app.profile_views
import app.setup_views
import app.beer_views
import app.api.lcd
import app.api.clog
import app.circus_views

admin.autodiscover()

# In addition to urlpatterns below, three paths are mapped by the nginx config file:
# r'^static/' - Maps to collected_static/. Contains collected static files.
# r'^media/' - Maps to media/. Contains uploaded files. Currently unused.
# r'^data/' - Maps to data/. Contains data points collected by brewpi.py.

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$', app.views.siteroot, name='siteroot'),

    url(r'^upgrade/$', app.views.github_trigger_upgrade, name='github_trigger_upgrade'),
    # url(r'^upgrade/$', app.views.github_trigger_upgrade, name='github_trigger_upgrade'),
    # url(r'^upgrade/$', app.views.github_trigger_upgrade, name='github_trigger_upgrade'),

    ### Device Views
    url(r'^devices/$', app.views.device_lcd_list, name='device_lcd_list'),
    url(r'^devices/add/$', app.views.add_device, name='device_add'),

    ## New install Guided Setup Views
    url(r'setup/$', app.setup_views.setup_splash, name="setup_splash"),
    url(r'setup/add_user/$', app.setup_views.setup_add_user, name="setup_add_user"),
    url(r'setup/settings/$', app.setup_views.setup_config, name="setup_config"),  # This is settings.CONSTANCE_SETUP_URL

    ## Device Guided Setup Views
    url(r'^devices/guided/$', app.setup_views.device_guided_select_device, name='device_guided_select_device'),
    url(r'^devices/guided/(?P<device_family>[A-Za-z0-9]{1,20})/flash_prompt/$', app.setup_views.device_guided_flash_prompt, name='device_guided_flash_prompt'),
    url(r'^devices/guided/(?P<device_family>[A-Za-z0-9]{1,20})/flash/$', app.setup_views.device_guided_flash_prompt, name='device_guided_flash_prompt'),
    url(r'^devices/guided/(?P<device_family>[A-Za-z0-9]{1,20})/connection/$', app.setup_views.device_guided_serial_wifi, name='device_guided_serial_wifi'),
    url(r'^devices/guided/mdns/$', app.setup_views.device_guided_find_mdns, name='device_guided_mdns'),
    url(r'^devices/guided/mdns/(?P<mdns_id>[A-Za-z0-9.]{1,60})/$', app.setup_views.device_guided_add_mdns, name='device_guided_add_mdns'),
    url(r'^devices/guided/serial/autodetect/(?P<device_family>[A-Za-z0-9]{1,20})/$', app.setup_views.device_guided_serial_autodetect, name='device_guided_serial_autodetect'),

    ## Other main device views
    url(r'^devices/(?P<device_id>\d{1,20})/control_constants/$', app.views.device_control_constants, name='device_control_constants'),
    url(r'^devices/(?P<device_id>\d{1,20})/dashboard/$', app.views.device_dashboard, name='device_dashboard'),
    url(r'^devices/(?P<device_id>\d{1,20})/dashboard/beer/(?P<beer_id>\d{1,20})/$', app.views.device_dashboard, name='device_dashboard_beer'),
    url(r'^devices/(?P<device_id>\d{1,20})/dashboard/beer/(?P<beer_id>\d{1,20})/annotations.json$', app.views.almost_json_view, name='almost_json_view'),
    # TODO - Implement backlight toggle AJAX API call
    url(r'^devices/(?P<device_id>\d{1,20})/backlight/toggle/$', app.views.device_dashboard, name='device_toggle_backlight'),
    # TODO - Implement temperature control AJAX API calls
    url(r'^devices/(?P<device_id>\d{1,20})/temp_control/$', app.views.device_temp_control, name='device_temp_control'),
    url(r'^devices/(?P<device_id>\d{1,20})/reset/$', app.views.device_eeprom_reset, name='device_eeprom_reset'),
    url(r'^devices/(?P<device_id>\d{1,20})/manage/$', app.views.device_manage, name='device_manage'),
    url(r'^devices/(?P<device_id>\d{1,20})/uninstall/$', app.views.device_uninstall, name='device_uninstall'),

    # Device Utility & Internal Views
    url(r'^devices/(?P<device_id>\d{1,20})/beer/create/$', app.beer_views.beer_create, name='beer_create'),
    url(r'^devices/(?P<device_id>\d{1,20})/beer/status/(?P<logging_status>[A-Za-z0-9]{1,20})/$', app.beer_views.beer_logging_status, name='beer_logging_status'),

    url(r'^devices/(?P<device_id>\d{1,20})/sensors/$', app.views.sensor_list, name='sensor_list'),
    url(r'^devices/(?P<device_id>\d{1,20})/sensors/config/$', app.views.sensor_config, name='sensor_config'),

    # Circus processmanager device views, we add device_name so we don't have to do another query
    url(r'^devices/(?P<device_id>\d{1,20})/proc/start/$', app.circus_views.start_brewpi_device, name='device_start'),
    url(r'^devices/(?P<device_id>\d{1,20})/proc/stop/$', app.circus_views.stop_brewpi_device, name='device_stop'),
    url(r'^devices/(?P<device_id>\d{1,20})/proc/remove/$', app.circus_views.remove_brewpi_device, name='device_remove'),
    url(r'^devices/(?P<device_id>\d{1,20})/proc/status/$', app.circus_views.status_brewpi_device, name='device_status'),
    

    # Fermentation Profile Views
    url(r'^fermentation_profile/list/$', app.profile_views.profile_list, name='profile_list'),
    url(r'^fermentation_profile/new/$', app.profile_views.profile_new, name='profile_new'),
    url(r'^fermentation_profile/(?P<profile_id>\d{1,20})/$', app.profile_views.profile_new, name='profile_view'),
    url(r'^fermentation_profile/(?P<profile_id>\d{1,20})/edit/$', app.profile_views.profile_edit, name='profile_edit'),
    url(r'^fermentation_profile/(?P<profile_id>\d{1,20})/delete/$', app.profile_views.profile_delete, name='profile_delete'),
    url(r'^fermentation_profile/(?P<profile_id>\d{1,20})/undelete/$', app.profile_views.profile_undelete, name='profile_undelete'),
    url(r'^fermentation_profile/(?P<profile_id>\d{1,20})/point/(?P<point_id>\d{1,20})/delete$', app.profile_views.profile_setpoint_delete, name='profile_setpoint_delete'),
    url(r'^fermentation_profile/(?P<profile_id>\d{1,20})/csv/$', app.profile_views.profile_points_to_csv, name='profile_points_to_csv'),

    # Api Views
    url(r'^api/lcd/(?P<device_id>\d{1,20})/$', app.api.lcd.getLCD, name="getLCD"),  # For a single device
    url(r'^api/lcd/$', app.api.lcd.getLCDs, name="getLCDs"),  # For all devices/LCDs
    url(r'^api/panel/(?P<device_id>\d{1,20})/$', app.api.lcd.getPanel, name="getPanel"),  # For a single device
    # Read controller log files
    url(r'^api/log/(?P<logfile>stdout|stderr)/(?P<device_id>\d{1,20})/$', app.api.clog.get_device_log_plain, name="get_device_log_plain"),
    url(r'^api/log/(?P<logfile>stdout|stderr)/(?P<device_id>\d{1,20})/(?P<lines>\d{1,20})/$', app.api.clog.get_device_log_plain, name="get_device_log_plain"),
    # Stdout JSON output (cleaned)
    url(r'^api/log/json/stdout/(?P<device_id>\d{1,20})/$', app.api.clog.get_stdout_as_json, name="get_stdout_as_json"),
    url(r'^api/log/json/stdout/(?P<device_id>\d{1,20})/(?P<lines>\d{1,20})/$', app.api.clog.get_stdout_as_json, name="get_stdout_as_json"),
    # Other logs
    url(r'^api/log/brewpi_spawner/$', app.api.clog.brewpi_spawner_log, name="brewpi_spawner_log"),
    url(r'^api/log/fermentrack/$', app.api.clog.fermentrack_log, name="fermentrack_log"),

    # Login/Logout Views
    url(r'^accounts/login/$', app.views.login, name='login'),  # This is also settings.LOGIN_URL
    url(r'^accounts/logout/$', app.views.logout, name='logout'),

    # Site-specific views (Help, Settings, etc.)
    url(r'site/settings/$', app.views.site_settings, name="site_settings"),
    url(r'site/help/$', app.views.site_help, name="site_help"),

] + static(settings.DATA_URL, document_root=settings.DATA_ROOT)  # To enable viewing data files during development
