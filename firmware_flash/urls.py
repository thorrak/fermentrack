from django.conf.urls import url
from django.contrib import admin

from django.conf import settings
from django.conf.urls.static import static

import firmware_flash.views


# This gets added
firmware_flash_urlpatterns = [
    ## Device Guided Setup Views
    url(r'^firmware/$', firmware_flash.views.firmware_select_family, name='firmware_flash_select_family'),
    url(r'^firmware/refresh/$', firmware_flash.views.firmware_refresh_list, name='firmware_flash_refresh_list'),
    url(r'^firmware/test/$', firmware_flash.views.firmware_refresh_list, name='firmware_flash_refresh_list'),

    url(r'^firmware/autodetect_serial/(?P<flash_family_id>[A-Za-z0-9]{1,20})/$',
        firmware_flash.views.firmware_flash_serial_autodetect, name='firmware_flash_serial_autodetect'),

    url(r'^firmware/select_firmware/(?P<flash_family_id>[A-Za-z0-9]{1,20})/$',
        firmware_flash.views.firmware_flash_select_firmware, name='firmware_flash_select_firmware'),

    url(r'^firmware/flash/(?P<flash_family_id>[A-Za-z0-9]{1,20})/$',
        firmware_flash.views.firmware_flash_flash_firmware, name='firmware_flash_flash_firmware'),

    # url(r'^devices/guided/(?P<device_family>[A-Za-z0-9]{1,20})/flash_prompt/$', app.setup_views.device_guided_flash_prompt, name='device_guided_flash_prompt'),
    # url(r'^devices/guided/(?P<device_family>[A-Za-z0-9]{1,20})/flash/$', app.setup_views.device_guided_flash_prompt, name='device_guided_flash_prompt'),
    # url(r'^devices/guided/(?P<device_family>[A-Za-z0-9]{1,20})/connection/$', app.setup_views.device_guided_serial_wifi, name='device_guided_serial_wifi'),
    # url(r'^devices/guided/mdns/$', app.setup_views.device_guided_find_mdns, name='device_guided_mdns'),
    # url(r'^devices/guided/mdns/(?P<mdns_id>[A-Za-z0-9.]{1,60})/$', app.setup_views.device_guided_add_mdns, name='device_guided_add_mdns'),
    # url(r'^devices/guided/serial/autodetect/(?P<device_family>[A-Za-z0-9]{1,20})/$', app.setup_views.device_guided_serial_autodetect, name='device_guided_serial_autodetect'),

]
