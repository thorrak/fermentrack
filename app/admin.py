from django.contrib import admin
from django.utils.safestring import mark_safe

from app.models import BrewPiDevice, Beer, FermentationProfile, FermentationProfilePoint

@admin.register(BrewPiDevice)
class brewPiDeviceAdmin(admin.ModelAdmin):
    list_display = ('device_name', 'temp_format', 'board_type', 'connection_type', 'wifi_host', 'serial_port')

@admin.register(Beer)
class beerAdmin(admin.ModelAdmin):
    list_display = ('name', 'device', 'created')

@admin.register(FermentationProfile)
class fermentationProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'image', 'status')
    readonly_fields = ('Profile_Picture',)

# used in the admin site model as a "thumbnail"
    def Profile_Picture(self, obj):
        return mark_safe('<img src="{url}" width="{width}" height={height} />'.format(
        url = obj.image.url,
        width=obj.image.width,
        height=obj.image.height,
        )
        )

@admin.register(FermentationProfilePoint)
class fermentationProfilePointAdmin(admin.ModelAdmin):
    list_display = ('profileName', 'temperature', 'ttl')

    def temperature(self, obj):
        return obj.temperature_setting, obj.temp_format

    def profileName(self, obj):
        return obj.profile.name
