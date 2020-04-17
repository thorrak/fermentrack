from django.conf.urls import url
from django.contrib import admin

from django.conf import settings
from django.conf.urls.static import static

import gravity.views
import gravity.views_ispindel
import gravity.views_tilt
import gravity.api.sensors

app_name = "gravity"

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
    url(r'^api/gravity/(?P<device_id>\d{1,20})/$', gravity.api.sensors.getGravitySensors, name="getSensor"),  # For a single device
    url(r'^api/gravity/$', gravity.api.sensors.getGravitySensors, name="getSensors"),  # For all sensors
    url(r'^api/gravity/ispindel/(?P<device_id>\d{1,20})/$', gravity.api.sensors.get_ispindel_extras, name="get_ispindel_extras"),  # Specific to iSpindel devices, allows for easy calibration
    url(r'^api/gravity/tilt/(?P<device_id>\d{1,20})/$', gravity.api.sensors.get_tilt_extras, name="get_tilt_extras"),  # Specific to Tilt Hydrometers, allows for easy calibration

    # iSpindel specific Views
    url(r'^i[sS]{1}pind[el]{2}/?$', gravity.views_ispindel.ispindel_handler, name="gravity_ispindel"),  # Handler for ispindel gravity readings
    url(r'^gravity/sensor/(?P<sensor_id>[A-Za-z0-9]{1,20})/ispindel/setup/$', gravity.views_ispindel.gravity_ispindel_setup, name='gravity_ispindel_setup'),
    url(r'^gravity/sensor/(?P<sensor_id>[A-Za-z0-9]{1,20})/ispindel/coefficients/$', gravity.views_ispindel.gravity_ispindel_coefficients, name='gravity_ispindel_coefficients'),
    url(r'^gravity/sensor/(?P<sensor_id>[A-Za-z0-9]{1,20})/ispindel/calibration/add/$', gravity.views_ispindel.gravity_ispindel_add_calibration_point, name='gravity_ispindel_add_calibration_point'),
    url(r'^gravity/sensor/(?P<sensor_id>[A-Za-z0-9]{1,20})/ispindel/calibration/delete/(?P<point_id>[A-Za-z0-9]{1,20})/$', gravity.views_ispindel.gravity_ispindel_delete_calibration_point, name='gravity_ispindel_delete_calibration_point'),
    url(r'^gravity/sensor/(?P<sensor_id>[A-Za-z0-9]{1,20})/ispindel/calibration/calibrate/$', gravity.views_ispindel.gravity_ispindel_calibrate, name='gravity_ispindel_calibrate'),
    url(r'^gravity/sensor/(?P<sensor_id>[A-Za-z0-9]{1,20})/ispindel/calibration/guided/(?P<step>[A-Za-z0-9]{1,20})$', gravity.views_ispindel.gravity_ispindel_guided_calibration, name='gravity_ispindel_guided_calibration'),

    # Tilt specific Views
    url(r'^[tT]{1}ilt[bB]{1}ridge/?$', gravity.views_tilt.tiltbridge_handler, name="gravity_tiltbridge"), # Handler for tiltbridge gravity readings
    # url(r'^gravity/sensor/(?P<sensor_id>[A-Za-z0-9]{1,20})/tilt/setup/$', gravity.views_tilt.gravity_tilt_setup, name='gravity_tilt_setup'),
    url(r'^gravity/sensor/(?P<sensor_id>[A-Za-z0-9]{1,20})/tilt/coefficients/gravity/$', gravity.views_tilt.gravity_tilt_coefficients, name='gravity_tilt_coefficients'),
    url(r'^gravity/sensor/(?P<sensor_id>[A-Za-z0-9]{1,20})/tilt/calibration/gravity/add/$', gravity.views_tilt.gravity_tilt_add_gravity_calibration_point, name='gravity_tilt_add_gravity_calibration_point'),
    url(r'^gravity/sensor/(?P<sensor_id>[A-Za-z0-9]{1,20})/tilt/calibration/gravity/delete/(?P<point_id>[A-Za-z0-9]{1,20})/$', gravity.views_tilt.gravity_tilt_delete_gravity_calibration_point, name='gravity_tilt_delete_gravity_calibration_point'),
    url(r'^gravity/sensor/(?P<sensor_id>[A-Za-z0-9]{1,20})/tilt/calibration/gravity/calibrate/$', gravity.views_tilt.gravity_tilt_calibrate, name='gravity_tilt_calibrate'),
    url(r'^gravity/sensor/(?P<sensor_id>[A-Za-z0-9]{1,20})/tilt/calibration/gravity/guided/(?P<step>[A-Za-z0-9]{1,20})$', gravity.views_tilt.gravity_tilt_guided_calibration, name='gravity_tilt_guided_calibration'),
    url(r'^gravity/tilt/test/$', gravity.views_tilt.gravity_tilt_test, name='gravity_tilt_test'),

    # TiltBridge specific views
    url(r'^gravity/tiltbridge/add/$', gravity.views_tilt.gravity_tiltbridge_add, name='gravity_tiltbridge_add'),
    url(r'^gravity/tiltbridge/update/(?P<tiltbridge_id>[A-Za-z0-9]{1,20})/set_url/$', gravity.views_tilt.gravity_tiltbridge_set_url, name='gravity_tiltbridge_set_url'),
    url(r'^gravity/tiltbridge/update/(?P<tiltbridge_id>[A-Za-z0-9]{1,20})/set_url/(?P<sensor_id>[A-Za-z0-9]{1,20})$', gravity.views_tilt.gravity_tiltbridge_set_url, name='gravity_tiltbridge_set_url'),
    url(r'^gravity/tiltbridge/urlerror/(?P<tiltbridge_id>[A-Za-z0-9]+)/$', gravity.views_tilt.gravity_tiltbridge_urlerror, name='gravity_tiltbridge_urlerror'),

]
