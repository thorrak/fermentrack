from django.contrib import admin

from gravity.models import GravitySensor, TiltConfiguration, IspindelConfiguration

@admin.register(GravitySensor)
class gravitySensorAdmin(admin.ModelAdmin):
    list_display = ('name', 'sensor_type', 'assigned_brewpi_device')

@admin.register(TiltConfiguration)
class tiltConfigurationAdmin(admin.ModelAdmin):
    list_display = ('sensor', 'color', )

@admin.register(IspindelConfiguration)
class ispindelConfigurationAdmin(admin.ModelAdmin):
    list_display = ('sensor', 'name_on_device', )

