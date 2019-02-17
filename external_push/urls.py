from django.conf.urls import url
from django.contrib import admin

from django.conf import settings
from django.conf.urls.static import static

import external_push.views


# This gets added to the app's urlpatterns
# TODO - Convert this to be properly namespaced
external_push_urlpatterns = [
    ## Device Guided Setup Views
    url(r'^push/$', external_push.views.external_push_list, name='external_push_list'),
    url(r'^push/add/$', external_push.views.external_push_generic_target_add, name='external_push_generic_target_add'),
    url(r'^push/view/(?P<push_target_id>[0-9]{1,20})/$', external_push.views.external_push_view, name='external_push_view'),
    url(r'^push/delete/(?P<push_target_id>[0-9]{1,20})/$', external_push.views.external_push_delete, name='external_push_delete'),

    # # Sensor Views
    # url(r'^gravity/sensor/(?P<sensor_id>[A-Za-z0-9]{1,20})/$', gravity.views.gravity_dashboard, name='gravity_dashboard'),
    # url(r'^gravity/sensor/(?P<sensor_id>[A-Za-z0-9]{1,20})/log/(?P<log_id>[A-Za-z0-9]{1,20})/view/$', gravity.views.gravity_dashboard, name='gravity_dashboard_log'),
    # url(r'^gravity/sensor/(?P<sensor_id>[A-Za-z0-9]{1,20})/attach/$', gravity.views.gravity_attach, name='gravity_attach'),
    # url(r'^gravity/sensor/(?P<sensor_id>[A-Za-z0-9]{1,20})/detach/$', gravity.views.gravity_detach, name='gravity_detach'),
    # url(r'^gravity/sensor/(?P<sensor_id>[A-Za-z0-9]{1,20})/uninstall/$', gravity.views.gravity_uninstall, name='gravity_uninstall'),
    # url(r'^gravity/sensor/(?P<sensor_id>[A-Za-z0-9]{1,20})/manage/$', gravity.views.gravity_manage, name='gravity_manage'),
    # url(r'^gravity/sensor/(?P<sensor_id>[A-Za-z0-9]{1,20})/log/(?P<log_id>[A-Za-z0-9]{1,20})/annotations.json$', gravity.views.almost_json_view, name='gravity_almost_json_view'),
    #
    # # Sensor Log Views
    # url(r'^gravity/sensor/(?P<sensor_id>[A-Za-z0-9]{1,20})/log/create/$', gravity.views.gravity_log_create, name='gravity_log_create'),
    # url(r'^gravity/sensor/(?P<sensor_id>[A-Za-z0-9]{1,20})/log/stop/$', gravity.views.gravity_log_stop, name='gravity_log_stop'),
    #
    # # Log Management
    # url(r'^gravity/logs/$', gravity.views.gravity_log_list, name='gravity_log_list'),
    # url(r'^gravity/logs/(?P<log_id>\d{1,20})/delete/$', gravity.views.gravity_log_delete, name='gravity_log_delete'),
    #
    # # API Calls
    # url(r'^api/gravity/(?P<device_id>\d{1,20})/$', gravity.api.sensors.getGravitySensors, name="getSensor"),  # For a single device
    # url(r'^api/gravity/$', gravity.api.sensors.getGravitySensors, name="getSensors"),  # For all sensors
    # url(r'^api/gravity/ispindel/(?P<device_id>\d{1,20})/$', gravity.api.sensors.get_ispindel_extras, name="get_ispindel_extras"),  # Specific to iSpindel devices, allows for easy calibration
    # url(r'^api/gravity/tilt/(?P<device_id>\d{1,20})/$', gravity.api.sensors.get_tilt_extras, name="get_tilt_extras"),  # Specific to Tilt Hydrometers, allows for easy calibration

]
