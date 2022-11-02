from django.db import models
from django_quill.fields import QuillField


class Intro(models.Model):
    class Meta:
        ordering = ("order",)
        verbose_name = "bulle de didacticiel"
        verbose_name_plural = "bulles de didacticiel"

    content = QuillField(verbose_name="contenu")
    title = models.CharField(verbose_name="titre", max_length=100)
    order = models.IntegerField(verbose_name="ordre dans la page")
    slug = models.CharField(verbose_name="identifiant", max_length=50)
    page = models.CharField(verbose_name="s'applique à la page", max_length=30)

    def __str__(self):
        return self.title
