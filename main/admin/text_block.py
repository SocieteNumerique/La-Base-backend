from django.contrib import admin
from django.contrib.admin.options import IncorrectLookupParameters
from django.db import models

from main.models import TextBlock

EMPTY_QUILL_CONTENT = '{"delta":"","html":""}'


class EmptyQuillContent(admin.EmptyFieldListFilter):
    def queryset(self, request, queryset):
        if self.lookup_kwarg not in self.used_parameters:
            return queryset
        if self.lookup_val not in ("0", "1"):
            raise IncorrectLookupParameters

        lookup_conditions = []
        if self.field.empty_strings_allowed:
            lookup_conditions.append((self.field_path, EMPTY_QUILL_CONTENT))
        if self.field.null:
            lookup_conditions.append((f"{self.field_path}__isnull", True))
        lookup_condition = models.Q(*lookup_conditions, _connector=models.Q.OR)
        if self.lookup_val == "1":
            return queryset.filter(lookup_condition)
        return queryset.exclude(lookup_condition)


@admin.register(TextBlock)
class IntroAdmin(admin.ModelAdmin):
    list_display = ("slug",)
    list_filter = (("content", EmptyQuillContent),)
