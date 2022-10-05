from django.contrib import admin

from main.models.page import Page


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ("title", "show_in_menu")
