from django.contrib import admin

from main.models import Intro


@admin.register(Intro)
class IntroAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "page")
