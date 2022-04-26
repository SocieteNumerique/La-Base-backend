from django.contrib import admin

from main.models import Base


@admin.register(Base)
class BaseAdmin(admin.ModelAdmin):
    list_display = ("title", "owner")
