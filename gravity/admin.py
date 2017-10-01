from django.contrib import admin

from gravity.models import GravitySensor

@admin.register(GravitySensor)
class gravitySensorAdmin(admin.ModelAdmin):
    list_display = ('name', 'sensor_type')

