from django.conf.urls import url
from django.contrib import admin

from django.conf import settings
from django.conf.urls.static import static



import brewery_image.views

# This gets added to the app's urlpatterns
# TODO - Convert this to be properly namespaced

brewery_image_urlpatterns = [
    ## Brewery Image Views (I have no idea what I'm doing)
    url(r'^brewery_image', brewery_image.views.display_brewery_images, name='brewery_image'),
    url(r'^image_upload', brewery_image.views.brewery_image, name = 'image_upload'),
    url(r'^success', brewery_image.views.index, name = 'success'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


#urlpatterns+={
#  path('',RedirectView.as_view(url='/brewery_image/',permanent=True))
# }

#if settings.DEBUG:
    #urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
