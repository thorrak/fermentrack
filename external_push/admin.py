from django.contrib import admin

from external_push.models import GenericPushTarget


@admin.register(GenericPushTarget)
class GenericPushTargetAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'target_host')
