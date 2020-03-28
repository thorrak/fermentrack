import os
from django.db import models
from django.conf import settings
from django.utils.safestring import mark_safe
from django.db.models.signals import post_delete
from django.dispatch.dispatcher import receiver
from django.db.models import DateTimeField

class BreweryLogo (models.Model):
    name = models.CharField(max_length=50, blank=True)
    image = models.ImageField(null=True, blank=True, default='/media/generic_logo.png')
    date = models.DateTimeField(auto_now=True)
    externalURL = models.URLField(blank=True)

# when uploading a new image through Admin, allows to pull image from external site
# default Fermentrack logo is displayed as image
    def url(self):
        # returns a URL for either internal stored or external image url
        if self.externalURL:
            return self.externalURL
        else:
            # is this the best way to do this??
            return os.path.join('/',settings.MEDIA_URL, os.path.basename(str(self.image)))

# used in the admin site model as a "thumbnail"
    def image_tag(self):
        return mark_safe('<img src="{}" width="25%" height="25%" />'.format(self.url()) )
    image_tag.short_description = 'Image'

    def __str__(self):
        return self.name

# this allows the use of {{ image.url }}, but only works for html in brewery_image templates
# how in the hell can I use something similar to display in app/sitewide/templates
@property
def image_url(self):
    if self.image:
        return self.image.url
    return '#'

#Deletes user uploaded file in Media Directory
@receiver(post_delete, sender=BreweryLogo)
def submission_delete(sender, instance, **kwargs):
    instance.image.delete(False)
