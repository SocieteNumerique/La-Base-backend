from django.contrib import admin

from main.models import Ressource


@admin.register(Ressource)
class RessourceAdmin(admin.ModelAdmin):
    pass
