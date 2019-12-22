from django.contrib import admin

from external_push.models import GenericPushTarget, BrewersFriendPushTarget, BrewfatherPushTarget, GrainfatherPushTarget


@admin.register(GenericPushTarget)
class GenericPushTargetAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'target_host')

@admin.register(BrewersFriendPushTarget)
class BrewersFriendPushTargetAdmin(admin.ModelAdmin):
    list_display = ('gravity_sensor_to_push', 'status', 'push_frequency')

@admin.register(BrewfatherPushTarget)
class BrewfatherPushTargetAdmin(admin.ModelAdmin):
    list_display = ('gravity_sensor_to_push', 'status', 'push_frequency')

@admin.register(GrainfatherPushTarget)
class GrainfatherPushTargetAdmin(admin.ModelAdmin):
    list_display = ('gravity_sensor_to_push', 'status', 'push_frequency')