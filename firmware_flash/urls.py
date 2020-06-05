from django.conf.urls import url
from django.contrib import admin

from django.conf import settings
from django.conf.urls.static import static

import firmware_flash.views

app_name = "firmware_flash"

# This gets added
firmware_flash_urlpatterns = [
    ## Device Guided Setup Views
    url(r'^firmware/$', firmware_flash.views.firmware_select_family, name='firmware_flash_select_family'),
    url(r'^firmware/refresh/$', firmware_flash.views.firmware_refresh_list, name='firmware_flash_refresh_list'),
    url(r'^firmware/autodetect_serial/(?P<board_id>[A-Za-z0-9]{1,20})/$', firmware_flash.views.firmware_flash_serial_autodetect, name='firmware_flash_serial_autodetect'),
    url(r'^firmware/select_board/(?P<flash_family_id>[A-Za-z0-9]{1,20})/$', firmware_flash.views.firmware_select_board, name='firmware_select_board'),
    url(r'^firmware/select_firmware/(?P<board_id>[A-Za-z0-9]{1,20})/$', firmware_flash.views.firmware_flash_select_firmware, name='firmware_flash_select_firmware'),
    url(r'^firmware/flash/(?P<board_id>[A-Za-z0-9]{1,20})/$', firmware_flash.views.firmware_flash_flash_firmware, name='firmware_flash_flash_firmware'),
    url(r'^firmware/status/(?P<flash_request_id>[0-9]{1,20})/$', firmware_flash.views.firmware_flash_flash_status, name='firmware_flash_flash_status'),

    # TODO - Delete the following once everything is confirmed working as expected
    # url(r'^firmware/test/$', firmware_flash.views.firmware_flash_test_select_firmware, name='firmware_flash_test_select_firmware'),

]
