from django.contrib import admin

from firmware_flash.models import DeviceFamily, Firmware, FlashRequest


@admin.register(DeviceFamily)
class deviceFamilyAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(Firmware)
class firmwareAdmin(admin.ModelAdmin):
    list_display = ('name', 'family', 'version', 'revision', 'variant',)


@admin.register(FlashRequest)
class flashRequestAdmin(admin.ModelAdmin):
    list_display = ('created', 'status', 'firmware_to_flash')
