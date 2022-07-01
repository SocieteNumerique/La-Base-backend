from django.contrib import admin

from main.models.models import Base


@admin.register(Base)
class BaseAdmin(admin.ModelAdmin):
    list_display = ("title", "owner")
    search_fields = ("title",)
    autocomplete_fields = [
        "owner",
        "admins",
        "tags",
        "contributor_tags",
        "pinned_resources",
        "pinned_collections",
    ]
