from django.contrib import admin

from main.models import Criterion


@admin.register(Criterion)
class CriterionAdmin(admin.ModelAdmin):
    pass
