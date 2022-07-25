from django.db import models

from main.models.models import Resource, Tag
from main.models.utils import TimeStampedModel
from main.query_changes.utils import query_my_related_tags


class ContentSection(TimeStampedModel):
    class Meta:
        verbose_name = "Dossier de contenu"
        verbose_name_plural = "Dossiers de contenu"
        ordering = ["order"]
        unique_together = ("resource", "order")

    resource = models.ForeignKey(Resource, models.CASCADE, related_name="sections")
    title = models.CharField(max_length=25, null=True, blank=True)
    is_foldable = models.BooleanField(default=False)
    order = models.BigIntegerField()


class ContentBlock(TimeStampedModel):
    class Meta:
        verbose_name = "Bloc de contenu"
        verbose_name_plural = "Blocs de contenu"
        ordering = ["order"]
        unique_together = ("order", "section")

    title = models.CharField(max_length=50, null=True, blank=True)
    annotation = models.TextField(null=True, blank=True)
    is_draft = models.BooleanField(default=True)
    resource = models.ForeignKey(Resource, models.CASCADE, related_name="contents")
    section = models.ForeignKey(ContentSection, models.CASCADE, related_name="contents")
    nb_col = models.IntegerField(default=2)
    order = models.BigIntegerField()
    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name="contents",
        limit_choices_to=query_my_related_tags("Content"),
    )
    use_resource_license_and_access = models.BooleanField(
        verbose_name="a les mêmes accès et licence que la ressource parente",
        default=False,
    )
    license_knowledge = models.CharField(
        choices=[
            ("specific", "Spécifique au contenu"),
            ("resource", "Identique à la ressource"),
            ("unknown", "Inconnue"),
        ],
        max_length=10,
        default="unknown",
    )
    license_text = models.ForeignKey(
        "main.LicenseText",
        verbose_name="Détail de licence propriétaire",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )


class LinkedResourceContent(ContentBlock):
    class Meta:
        verbose_name = "Contenu : Ressource liée"
        verbose_name_plural = "Contenus : Ressources liées"

    linked_resource = models.ForeignKey(
        Resource, models.SET_NULL, null=True, blank=True
    )


class LinkContent(ContentBlock):
    class Meta:
        verbose_name = "Contenu : Lien externe"
        verbose_name_plural = "Contenus : Liens externes"

    link = models.URLField(blank=True, null=True)
    with_preview = models.BooleanField(default=False)


class TextContent(ContentBlock):
    class Meta:
        verbose_name = "Contenu : Texte"
        verbose_name_plural = "Contenus : Textes"

    text = models.TextField(blank=True, null=True)  # TODO add rich text support


class FileContent(ContentBlock):
    class Meta:
        verbose_name = "Contenu : Fichier importé"
        verbose_name_plural = "Contenus : Fichiers importés"

    file = models.FileField()
    with_preview = models.BooleanField(default=False)
