from django.conf.urls import url
from django.contrib import admin

from django.conf import settings
from django.conf.urls.static import static



import brewery_image.views

# This gets added to the app's urlpatterns
# TODO - Convert this to be properly namespaced

brewery_image_urlpatterns = [
    ## Brewery Image Views (I kinda have an idea what I'm doing)
    url(r'^image/$', brewery_image.views.display_brewery_images, name='brewery_images'),
]
