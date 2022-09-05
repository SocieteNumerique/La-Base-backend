from django.contrib import admin

from main.models.models import Base


@admin.register(Base)
class BaseAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "instance_visit_count")
    search_fields = ("title",)
    autocomplete_fields = [
        "owner",
        "admins",
        "tags",
        "authorized_users",
        "authorized_user_tags",
        "contributors",
        "contributor_tags",
        "pinned_resources",
        "pinned_collections",
    ]
