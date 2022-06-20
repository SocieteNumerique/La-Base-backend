from django.contrib import admin

from main.models.models import Tag


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "category")
    search_fields = ("name",)
