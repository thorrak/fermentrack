from django.conf.urls import url
from django.contrib import admin

from django.conf import settings
from django.conf.urls.static import static

import gravity.views
import gravity.api.sensors


# This gets added to the app's urlpatterns
gravity_urlpatterns = [
    ## Device Guided Setup Views
    url(r'^gravity/$', gravity.views.gravity_list, name='gravity_list'),
    url(r'^gravity/add/$', gravity.views.gravity_add_board, name='gravity_add_board'),
    url(r'^gravity/manual_point/(?P<manual_sensor_id>[A-Za-z0-9]{1,20})/$', gravity.views.gravity_add_point, name='gravity_add_point'),
    # url(r'^gravity/add/tilt/$', firmware_flash.views.firmware_refresh_list, name='firmware_flash_refresh_list'),
    # url(r'^gravity/add/tilt/$', firmware_flash.views.firmware_refresh_list, name='firmware_flash_refresh_list'),

    url(r'^gravity/(?P<sensor_id>[A-Za-z0-9]{1,20})/$', gravity.views.gravity_dashboard, name='gravity_dashboard'),
    url(r'^gravity/(?P<sensor_id>[A-Za-z0-9]{1,20})/log/(?P<log_id>[A-Za-z0-9]{1,20})/view/$', gravity.views.gravity_dashboard, name='gravity_dashboard_log'),
    url(r'^gravity/(?P<sensor_id>[A-Za-z0-9]{1,20})/attach/$', gravity.views.gravity_dashboard, name='gravity_attach'),
    url(r'^gravity/(?P<sensor_id>[A-Za-z0-9]{1,20})/detach/$', gravity.views.gravity_dashboard, name='gravity_detach'),

    url(r'^gravity/(?P<sensor_id>[A-Za-z0-9]{1,20})/log/create/$', gravity.views.gravity_log_create, name='gravity_log_create'),

    # url(r'^firmware/autodetect_serial/(?P<board_id>[A-Za-z0-9]{1,20})/$', firmware_flash.views.firmware_flash_serial_autodetect, name='firmware_flash_serial_autodetect'),
    # url(r'^firmware/select_board/(?P<flash_family_id>[A-Za-z0-9]{1,20})/$', firmware_flash.views.firmware_select_board, name='firmware_select_board'),
    # url(r'^firmware/select_firmware/(?P<board_id>[A-Za-z0-9]{1,20})/$', firmware_flash.views.firmware_flash_select_firmware, name='firmware_flash_select_firmware'),
    # url(r'^firmware/flash/(?P<board_id>[A-Za-z0-9]{1,20})/$', firmware_flash.views.firmware_flash_flash_firmware, name='firmware_flash_flash_firmware'),

    # TODO - Delete the following once everything is confirmed working as expected
    # url(r'^firmware/test/$', firmware_flash.views.firmware_flash_test_select_firmware, name='firmware_flash_test_select_firmware'),

    url(r'^api/gravity/(?P<device_id>\d{1,20})/$', gravity.api.sensors.getGravitySensors, name="getSensor"),  # For a single device
    url(r'^api/gravity/$', gravity.api.sensors.getGravitySensors, name="getSensors"),  # For all sensors

]
