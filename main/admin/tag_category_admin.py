from django.contrib import admin

from main.models import TagCategory


@admin.register(TagCategory)
class TagCategoryAdmin(admin.ModelAdmin):
    # list_display = ("name", "category")
    pass
