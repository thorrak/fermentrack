"""brewpi_django URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin

import app.views
import app.profile_views
import app.api.lcd

admin.autodiscover()

import app.views

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^lcd_test/$', app.views.lcd_test, name='lcd_test'),
    url(r'^$', app.views.siteroot, name='siteroot'),

    ### Device Views
    url(r'^devices/$', app.views.device_list, name='device_list'),
    url(r'^devices/add/$', app.views.add_device, name='device_add'),
    url(r'^devices/mdns/$', app.views.find_new_mdns_brewpi_controller, name='device_mdns'),

    url(r'^devices/(?P<device_id>\d{1,20})/config/$', app.views.device_config, name='device_config'),
    url(r'^devices/(?P<device_id>\d{1,20})/dashboard/$', app.views.device_dashboard, name='device_dashboard'),

    # Device Utility & Internal Views
    url(r'^devices/(?P<device_id>\d{1,20})/beer/csv/active_beer.csv$', app.views.beer_active_csv, name='csv_active_beer'),
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

]
