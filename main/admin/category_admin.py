from django.contrib import admin

from main.models import Category, RessourceCategory


class RessourceInline(admin.TabularInline):
    model = RessourceCategory


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("base", "title")
    inlines = (RessourceInline,)
