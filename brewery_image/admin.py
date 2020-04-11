from django.contrib import admin

from brewery_image.models import BreweryLogo

@admin.register(BreweryLogo)
class BreweryLogoAdmin(admin.ModelAdmin):
    list_display = ('brewery_name', 'image', 'externalURL',)
    readonly_fields = ('image_tag', 'date')
