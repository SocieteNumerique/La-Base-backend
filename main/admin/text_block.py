from django.contrib import admin

from main.models import TextBlock


@admin.register(TextBlock)
class IntroAdmin(admin.ModelAdmin):
    list_display = ("slug",)
