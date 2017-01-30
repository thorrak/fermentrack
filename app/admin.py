from django.contrib import admin

from app.models import BrewPiDevice, Beer, BeerLogPoint, FermentationProfile, FermentationProfilePoint

@admin.register(BrewPiDevice)
class brewPiDeviceAdmin(admin.ModelAdmin):
    list_display = ('device_name', 'temp_format', 'connection_type', 'wifi_host', 'serial_port')

@admin.register(Beer)
class beerAdmin(admin.ModelAdmin):
    list_display = ('name', 'device', 'created')

@admin.register(BeerLogPoint)
class beerLogPointAdmin(admin.ModelAdmin):
    list_display = ('associated_beer', 'log_time', 'beer_temp', 'fridge_temp')

@admin.register(FermentationProfile)
class fermentationProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'status')

@admin.register(FermentationProfilePoint)
class fermentationProfilePointAdmin(admin.ModelAdmin):
    list_display = ('profileName', 'temperature', 'ttl')

    def temperature(self, obj):
        return obj.temperature_setting, obj.temp_format

    def profileName(self, obj):
        return obj.profile.name

