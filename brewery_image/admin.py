from django.contrib import admin

from brewery_image.models import Image

@admin.register(Image)
class imageAdmin(admin.ModelAdmin):
    list_display = ('name', 'image', 'externalURL')
    readonly_fields = ('image_tag',)
