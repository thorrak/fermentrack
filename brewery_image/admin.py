from django.contrib import admin

from brewery_image.models import BreweryLogo

@admin.register(BreweryLogo)
class BreweryLogoAdmin(admin.ModelAdmin):
    list_display = ('name', 'image', 'externalURL')
    readonly_fields = ('image_tag',)
