from django.contrib import admin

from main.models import Resource, TextContent


class TextContentInline(admin.TabularInline):
    model = TextContent


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    inlines = [TextContentInline]
    filter_horizontal = ["linked_resources"]
