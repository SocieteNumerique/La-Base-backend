from django.db import models
from django.utils.safestring import mark_safe
from django_quill.fields import QuillField

from main.models.utils import TimeStampedModel


class TextBlock(TimeStampedModel):
    class Meta:
        verbose_name = "bloc de texte"
        verbose_name_plural = "blocs de texte"

    content = QuillField(verbose_name="contenu", null=True, blank=True)
    slug = models.CharField(
        primary_key=True,
        verbose_name="identifiant",
        max_length=50,
        help_text=mark_safe(
            "<b>Ne pas faire de bêtise avec ce champ !</b> En général, il n'a pas besoin d'être modifié."
        ),
    )

    def __str__(self):
        return self.slug


TEXT_BLOCKS = [
    "homeSearchBlockDescription",
    "homeSearchBlockContent",
    "homeSearchBlockContentMore",
    "homeAccountBlockDescription",
    "homeAccountBlockContent",
    "homeAccountBlockContentMore",
    "homeResourcesBlockDescription",
    "homeResourcesBlockContent",
    "homeResourcesBlockContentMore",
    "homeBasesBlockDescription",
    "homeBasesBlockContent",
    "homeBasesBlockContentMore",
    "homeIntroLeft",
    "homeIntroRight",
    "homeIntroFarRight",
    "baseCertificationModal",
]
