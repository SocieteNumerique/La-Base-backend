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
    title = models.CharField(max_length=100, null=True, blank=True)
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
        default=True,
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
    license_text = models.OneToOneField(
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
    with_preview = models.BooleanField(default=True)
    target_image = models.URLField(null=True, blank=True)
    target_description = models.CharField(max_length=180, null=True, blank=True)
    target_title = models.CharField(max_length=80, null=True, blank=True)

    def save(self, **kwargs):
        # always try to fetch target metadata, even if it exists, as the link
        # target might have changed
        from linkpreview import link_preview

        try:
            preview = link_preview(self.link)
        except Exception:
            pass
        else:
            # there was no exception
            self.target_image = preview.absolute_image and preview.absolute_image[:200]
            self.target_description = preview.description and preview.description[:180]
            self.target_title = preview.force_title and preview.force_title[:80]
        super().save(**kwargs)


class TextContent(ContentBlock):
    class Meta:
        verbose_name = "Contenu : Texte"
        verbose_name_plural = "Contenus : Textes"

    text = models.TextField(blank=True, null=True)  # TODO add rich text support


class FileContent(ContentBlock):
    class Meta:
        verbose_name = "Contenu : Fichier importé"
        verbose_name_plural = "Contenus : Fichiers importés"

    image_alt = models.CharField(null=True, blank=True, max_length=100)
    file = models.FileField()
    with_preview = models.BooleanField(default=False)
