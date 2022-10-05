from django.db import models
from django_quill.fields import QuillField

from main.models.utils import TimeStampedModel


class Page(TimeStampedModel):
    title = models.CharField(max_length=50, verbose_name="titre")
    icon = models.CharField(
        max_length=50,
        verbose_name="icone",
        help_text="nom de l'icone remix icon, type ri-search-line",
    )
    show_in_menu = models.BooleanField(
        verbose_name="faire apparaitre la page dans le menu", default=False
    )
    description = models.CharField(verbose_name="description (SEO)", max_length=180)
    content = QuillField()

    def __str__(self):
        return self.title
