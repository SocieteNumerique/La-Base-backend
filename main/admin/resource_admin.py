from django.contrib import admin

from main.models import Resource, TextContent, FileContent, ContentSection


class ContentSectionInline(admin.TabularInline):
    model = ContentSection


class TextContentInline(admin.TabularInline):
    model = TextContent


class FileContentInline(admin.TabularInline):
    model = FileContent


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    inlines = [TextContentInline, FileContentInline, ContentSectionInline]
    filter_horizontal = ["linked_resources"]
