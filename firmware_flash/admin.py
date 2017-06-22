from django.contrib import admin

from firmware_flash.models import DeviceFamily, Firmware

@admin.register(DeviceFamily)
class deviceFamilyAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Firmware)
class firmwareAdmin(admin.ModelAdmin):
    list_display = ('name', 'family', 'version', 'revision', 'variant',)
