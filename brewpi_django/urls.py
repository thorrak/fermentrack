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

admin.autodiscover()

import app.views

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^lcd_test/$', app.views.lcd_test, name='lcd_test'),
    url(r'^$', app.views.siteroot, name='siteroot'),

    ### Device Views
    url(r'^devices/$', app.views.device_list, name='device_list'),
    url(r'^devices/add/$', app.views.add_device, name='device_add'),

    url(r'^devices/(\d{1,20})/config/$', app.views.device_config, name='device_config'),
    url(r'^devices/(\d{1,20})/dashboard/$', app.views.device_dashboard, name='device_dashboard'),

    # Device Utility & Internal Views
    url(r'^devices/(\d{1,20})/beer/csv/active_beer.csv$', app.views.beer_active_csv, name='csv_active_beer'),
    # url(r'^devices/(\d{1,20})/beer/csv/(\d{1,20}).csv$', app.views.device_config, name='csv_numbered'),

    url(r'^devices/(?P<device_id>\d{1,20})/sensors/$', app.views.sensor_list, name='sensor_list'),
    url(r'^devices/(?P<device_id>\d{1,20})/sensors/config/$', app.views.sensor_config, name='sensor_config'),

    # Fermentation Profile Views
    # TODO - Add views for fermentation profile that won't lose the device ID
    url(r'^fermentation_profile/new/$', app.views.beer_active_csv, name='profile_new'),
    url(r'^fermentation_profile/(\d{1,20})/$', app.views.beer_active_csv, name='profile_view'),

]
