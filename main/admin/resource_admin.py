from django.contrib import admin

from main.models import Resource


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    pass
