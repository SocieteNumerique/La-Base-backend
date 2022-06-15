from django.contrib import admin

from main.models.models import Resource
from main.models.contents import TextContent, FileContent, ContentSection


class ContentSectionInline(admin.TabularInline):
    model = ContentSection


class TextContentInline(admin.TabularInline):
    model = TextContent


class FileContentInline(admin.TabularInline):
    model = FileContent


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    inlines = [TextContentInline, FileContentInline, ContentSectionInline]
