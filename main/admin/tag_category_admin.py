from django.contrib import admin

from main.models.models import TagCategory, Tag


class TagInline(admin.TabularInline):
    model = Tag


@admin.register(TagCategory)
class TagCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "relates_to")
    inlines = [TagInline]
