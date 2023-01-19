from django.db import models
from django_quill.fields import QuillField

from main.models.utils import TimeStampedModel


class Page(TimeStampedModel):
    class Meta:
        ordering = ("order",)

    content = QuillField(
        help_text="Pour ajouter des champs ALT aux images, ajouter du texte commençant par ALT juste en-dessous de l'image."
    )
    description = models.CharField(verbose_name="description (SEO)", max_length=180)
    icon = models.CharField(
        max_length=50,
        verbose_name="icone",
        help_text="nom de l'icone remix icon, type ri-search-line",
        blank=True,
        default="",
    )
    order = models.IntegerField(verbose_name="ordre dans le menu")
    show_in_menu = models.BooleanField(
        verbose_name="faire apparaitre la page dans le menu", default=False
    )
    slug = models.CharField(
        verbose_name="slug",
        help_text="nom de la page dans l'URL",
        max_length=100,
        primary_key=True,
    )
    title = models.CharField(max_length=50, verbose_name="titre")

    def __str__(self):
        return self.title
