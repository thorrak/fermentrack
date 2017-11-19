from django.contrib import admin

from gravity.models import GravitySensor, TiltConfiguration

@admin.register(GravitySensor)
class gravitySensorAdmin(admin.ModelAdmin):
    list_display = ('name', 'sensor_type', 'assigned_brewpi_device')

@admin.register(TiltConfiguration)
class tiltConfigurationAdmin(admin.ModelAdmin):
    list_display = ('sensor', 'color', )

