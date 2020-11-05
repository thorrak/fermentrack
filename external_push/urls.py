from django.conf.urls import url
from django.contrib import admin

from django.conf import settings
from django.conf.urls.static import static

import external_push.views

app_name = "external_push"

# This gets added to the app's urlpatterns
# TODO - Convert this to be properly namespaced
external_push_urlpatterns = [
    ## External Push Views
    url(r'^push/$', external_push.views.external_push_list, name='external_push_list'),
    url(r'^push/add/$', external_push.views.external_push_generic_target_add, name='external_push_generic_target_add'),
    url(r'^push/view/(?P<push_target_id>[0-9]{1,20})/$', external_push.views.external_push_view, name='external_push_view'),
    url(r'^push/delete/(?P<push_target_id>[0-9]{1,20})/$', external_push.views.external_push_delete, name='external_push_delete'),

    url(r'^push/brewersfriend/add/$', external_push.views.external_push_brewers_friend_target_add, name='external_push_brewers_friend_target_add'),
    url(r'^push/brewersfriend/view/(?P<push_target_id>[0-9]{1,20})/$', external_push.views.external_push_brewers_friend_view, name='external_push_brewers_friend_view'),
    url(r'^push/brewersfriend/delete/(?P<push_target_id>[0-9]{1,20})/$', external_push.views.external_push_brewers_friend_delete, name='external_push_brewers_friend_delete'),

    url(r'^push/brewfather/add/$', external_push.views.external_push_brewfather_target_add, name='external_push_brewfather_target_add'),
    url(r'^push/brewfather/view/(?P<push_target_id>[0-9]{1,20})/$', external_push.views.external_push_brewfather_view, name='external_push_brewfather_view'),
    url(r'^push/brewfather/delete/(?P<push_target_id>[0-9]{1,20})/$', external_push.views.external_push_brewfather_delete, name='external_push_brewfather_delete'),

    url(r'^push/thingspeak/add/$', external_push.views.external_push_thingspeak_target_add, name='external_push_thingspeak_target_add'),
    url(r'^push/thingspeak/view/(?P<push_target_id>[0-9]{1,20})/$', external_push.views.external_push_thingspeak_view, name='external_push_thingspeak_view'),
    url(r'^push/thingspeak/delete/(?P<push_target_id>[0-9]{1,20})/$', external_push.views.external_push_thingspeak_delete, name='external_push_thingspeak_delete'),

    url(r'^push/grainfather/add/$', external_push.views.external_push_grainfather_target_add, name='external_push_grainfather_target_add'),
    url(r'^push/grainfather/view/(?P<push_target_id>[0-9]{1,20})/$', external_push.views.external_push_grainfather_view, name='external_push_grainfather_view'),
    url(r'^push/grainfather/delete/(?P<push_target_id>[0-9]{1,20})/$', external_push.views.external_push_grainfather_delete, name='external_push_grainfather_delete'),
]
