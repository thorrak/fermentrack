from django.contrib import admin

from app.models import InstallSettings, BrewPiDevice, Beer, BeerLogPoint

@admin.register(InstallSettings)
class installSettingsAdmin(admin.ModelAdmin):
    list_display = ('date_time_format', 'date_time_format_display')

@admin.register(BrewPiDevice)
class brewPiDeviceAdmin(admin.ModelAdmin):
    list_display = ('device_name', 'temp_format', 'has_old_brewpi_www', 'connection_type', 'wifi_host', 'serial_port')

@admin.register(Beer)
class beerAdmin(admin.ModelAdmin):
    list_display = ('name', 'device', 'created')

@admin.register(BeerLogPoint)
class beerLogPointAdmin(admin.ModelAdmin):
    list_display = ('associated_beer', 'log_time', 'beer_temp', 'fridge_temp')

# admin.site.register(InstallSettings, installSettingsAdmin)
# admin.site.register(BrewPiDevice, brewPiDeviceAdmin)
#admin.site.register(structureTimer, structureTimerAdmin)

