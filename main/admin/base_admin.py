from django.contrib import admin

from main.models import Base, Category


class CategoryInline(admin.TabularInline):
    model = Category


@admin.register(Base)
class BaseAdmin(admin.ModelAdmin):
    list_display = ("title", "owner")
    inlines = (CategoryInline,)
