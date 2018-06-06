from django.conf.urls import url
from django.contrib import admin

from django.conf import settings
from django.conf.urls.static import static

import gravity.views
import gravity.views_ispindel
import gravity.api.sensors


# This gets added to the app's urlpatterns
gravity_urlpatterns = [
    ## Device Guided Setup Views
    url(r'^gravity/$', gravity.views.gravity_list, name='gravity_list'),
    url(r'^gravity/add/$', gravity.views.gravity_add_board, name='gravity_add_board'),
    url(r'^gravity/manual_point/(?P<manual_sensor_id>[A-Za-z0-9]{1,20})/$', gravity.views.gravity_add_point, name='gravity_add_point'),
    # url(r'^gravity/add/tilt/$', firmware_flash.views.firmware_refresh_list, name='firmware_flash_refresh_list'),
    # url(r'^gravity/add/tilt/$', firmware_flash.views.firmware_refresh_list, name='firmware_flash_refresh_list'),

    # Sensor Views
    url(r'^gravity/sensor/(?P<sensor_id>[A-Za-z0-9]{1,20})/$', gravity.views.gravity_dashboard, name='gravity_dashboard'),
    url(r'^gravity/sensor/(?P<sensor_id>[A-Za-z0-9]{1,20})/log/(?P<log_id>[A-Za-z0-9]{1,20})/view/$', gravity.views.gravity_dashboard, name='gravity_dashboard_log'),
    url(r'^gravity/sensor/(?P<sensor_id>[A-Za-z0-9]{1,20})/attach/$', gravity.views.gravity_attach, name='gravity_attach'),
    url(r'^gravity/sensor/(?P<sensor_id>[A-Za-z0-9]{1,20})/detach/$', gravity.views.gravity_detach, name='gravity_detach'),
    url(r'^gravity/sensor/(?P<sensor_id>[A-Za-z0-9]{1,20})/uninstall/$', gravity.views.gravity_uninstall, name='gravity_uninstall'),
    url(r'^gravity/sensor/(?P<sensor_id>[A-Za-z0-9]{1,20})/manage/$', gravity.views.gravity_manage, name='gravity_manage'),
    url(r'^gravity/sensor/(?P<sensor_id>[A-Za-z0-9]{1,20})/log/(?P<log_id>[A-Za-z0-9]{1,20})/annotations.json$', gravity.views.almost_json_view, name='gravity_almost_json_view'),

    # Sensor Log Views
    url(r'^gravity/sensor/(?P<sensor_id>[A-Za-z0-9]{1,20})/log/create/$', gravity.views.gravity_log_create, name='gravity_log_create'),
    url(r'^gravity/sensor/(?P<sensor_id>[A-Za-z0-9]{1,20})/log/stop/$', gravity.views.gravity_log_stop, name='gravity_log_stop'),

    # Log Management
    url(r'^gravity/logs/$', gravity.views.gravity_log_list, name='gravity_log_list'),
    url(r'^gravity/logs/(?P<log_id>\d{1,20})/delete/$', gravity.views.gravity_log_delete, name='gravity_log_delete'),

    # API Calls
    # TODO - rename views below to prepend 'gravity'
    url(r'^api/gravity/(?P<device_id>\d{1,20})/$', gravity.api.sensors.getGravitySensors, name="getSensor"),  # For a single device
    url(r'^api/gravity/$', gravity.api.sensors.getGravitySensors, name="getSensors"),  # For all sensors
    url(r'^api/gravity/ispindel/(?P<device_id>\d{1,20})/$', gravity.api.sensors.getIspindelExtras, name="getIspindelExtras"),  # Specific to iSpindel devices, allows for easy calibration

    # iSpindel-specific Views
    url(r'^i[sS]{1}pind[el]{2}/?$', gravity.views_ispindel.ispindel_handler, name="gravity_ispindel"),  # Handler for ispindel gravity readings
    url(r'^gravity/sensor/(?P<sensor_id>[A-Za-z0-9]{1,20})/ispindel/setup/$', gravity.views_ispindel.gravity_ispindel_setup, name='gravity_ispindel_setup'),
    url(r'^gravity/sensor/(?P<sensor_id>[A-Za-z0-9]{1,20})/ispindel/coefficients/$', gravity.views_ispindel.gravity_ispindel_coefficients, name='gravity_ispindel_coefficients'),
    url(r'^gravity/sensor/(?P<sensor_id>[A-Za-z0-9]{1,20})/ispindel/calibration/add/$', gravity.views_ispindel.gravity_ispindel_add_calibration_point, name='gravity_ispindel_add_calibration_point'),
    url(r'^gravity/sensor/(?P<sensor_id>[A-Za-z0-9]{1,20})/ispindel/calibration/delete/(?P<point_id>[A-Za-z0-9]{1,20})/$', gravity.views_ispindel.gravity_ispindel_delete_calibration_point, name='gravity_ispindel_delete_calibration_point'),
    url(r'^gravity/sensor/(?P<sensor_id>[A-Za-z0-9]{1,20})/ispindel/calibration/calibrate/$', gravity.views_ispindel.gravity_ispindel_calibrate, name='gravity_ispindel_calibrate'),
    url(r'^gravity/sensor/(?P<sensor_id>[A-Za-z0-9]{1,20})/ispindel/calibration/guided/(?P<step>[A-Za-z0-9]{1,20})$', gravity.views_ispindel.gravity_ispindel_guided_calibration, name='gravity_ispindel_guided_calibration'),

]
