from django.contrib import admin

from main.models import Collection


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ("name", "base")
    search_fields = ("name",)
