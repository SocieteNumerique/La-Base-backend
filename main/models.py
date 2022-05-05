from django.db import models
from telescoop_auth.models import User


class TimeStampedModel(models.Model):
    """
    An abstract base class model that provides self-updating
    ``created`` and ``modified`` fields.

    """

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateField(auto_now=True)

    class Meta:
        abstract = True


class Base(TimeStampedModel):
    title = models.CharField(max_length=100)
    owner = models.ForeignKey(User, models.CASCADE, related_name="owner")
    admins = models.ManyToManyField(User, related_name="admins")

    def __str__(self):
        return self.title


class ContributorProfile(TimeStampedModel):
    class Meta:
        verbose_name = "Profil de contributeur"

    name = models.CharField(max_length=100)
    base = models.ForeignKey(Base, models.CASCADE, related_name="contributor_profiles")
    contributors = models.ManyToManyField(User)

    # TODO autorisations

    def __str__(self):
        return f"{self.base} - {self.name}"


class TagCategory(TimeStampedModel):
    class Meta:
        unique_together = ("name", "base")
        verbose_name = "Catégorie de tags"
        verbose_name_plural = "Catégories de tags"

    name = models.CharField(verbose_name="nom", max_length=20)
    description = models.CharField(
        verbose_name="description", null=True, max_length=100
    )
    required_to_be_public = models.BooleanField(
        verbose_name="remplissage obligatoire pour passer en public", default=False
    )
    maximum_tag_count = models.PositiveSmallIntegerField(
        verbose_name="nombre maximum de tags liés", null=True, blank=True
    )
    is_multi_select = models.BooleanField(
        verbose_name="plusieurs choix possibles", default=False
    )
    accepts_free_tags = models.BooleanField(
        verbose_name="accepte des tags libres", default=True
    )
    relates_to = models.CharField(
        max_length=10,
        verbose_name="lié aux",
        choices=[
            ("Resource", "Ressources"),
            ("User", "Utilisateurs"),
            ("Base", "Bases"),
        ],
    )  # no user in v1
    is_draft = models.BooleanField(
        verbose_name="est un brouillon",
        default=False,
        help_text="Une catégorie en brouillon est ignorée par l'appli",
    )
    base = models.ForeignKey(
        Base,
        models.CASCADE,
        verbose_name="lié à la base",
        null=True,
        blank=True,
        help_text="si une catégorie de tag n'est liée à aucune base, elle est globale",
    )

    def __str__(self):
        return f"{self.base or 'GLOBAL'} - {self.name}"


class Tag(TimeStampedModel):
    class Meta:
        unique_together = ("name", "category")

    name = models.CharField(verbose_name="nom", max_length=20)
    category = models.ForeignKey(
        TagCategory, on_delete=models.CASCADE, related_name="tags"
    )
    parent_tag = models.ForeignKey(
        "self",
        models.CASCADE,
        verbose_name="parent",
        null=True,
        blank=True,
        related_name="tags",
    )
    is_free = models.BooleanField(verbose_name="est un tag libre", default=False)
    is_draft = models.BooleanField(verbose_name="est un brouillon", default=False)
    definition = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.category.base or 'GLOBAL'} - {self.name}"


class Resource(TimeStampedModel):
    class Meta:
        verbose_name = "Ressource"

    title = models.CharField(max_length=100)
    creator = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="creator"
    )
    root_base = models.ForeignKey(Base, on_delete=models.PROTECT)
    is_draft = models.BooleanField(default=True)
    description = models.CharField(
        max_length=60, null=True, blank=True
    )  # only if not in base, first
    zip_code = models.IntegerField(null=True, blank=True)
    url = models.URLField(null=True, blank=True)
    thumbnail = models.ImageField(null=True, blank=True)
    linked_resources = models.ManyToManyField("self", blank=True)
    internal_producers = models.ManyToManyField(
        User, blank=True, related_name="internal_producers"
    )
    tags = models.ManyToManyField(Tag, blank=True)

    def missing_categories_to_be_public(self):
        filled_required_tag_categories = {
            tag.category
            for tag in self.tags.all()
            if tag.category.required_to_be_public and tag.category.tags.count() > 0
        }
        return (
            set(TagCategory.objects.filter(required_to_be_public=True).all())
            - filled_required_tag_categories
        )

    def is_allowed_to_be_public(self):
        return len(self.missing_categories_to_be_public()) > 0

    def __str__(self):
        return self.title


class ExternalProducer(TimeStampedModel):
    class Meta:
        verbose_name = "Producteur sans compte sur la plateforme"
        verbose_name_plural = "Producteurs sans compte sur la plateforme"

    name = models.CharField(max_length=100)
    email_contact = models.EmailField()
    validated = models.BooleanField(default=False)
    resource = models.ForeignKey(
        Resource, models.CASCADE, related_name="external_producer"
    )

    # tags

    def __str__(self):
        return f"EXT - ${self.name}"


class ContentSection(TimeStampedModel):
    class Meta:
        verbose_name = "Dossier de contenu"
        verbose_name_plural = "Dossiers de contenu"

    resource = models.ForeignKey(Resource, models.CASCADE)
    title = models.CharField(max_length=20)


class ContentBlock(TimeStampedModel):
    class Meta:
        verbose_name = "Bloc de contenu"
        verbose_name_plural = "Blocs de contenu"
        ordering = ["order"]
        unique_together = ("resource", "order", "section")

    title = models.CharField(max_length=20, null=True)
    annotation = models.TextField(null=True, blank=True)
    is_draft = models.BooleanField(default=True)
    resource = models.ForeignKey(Resource, models.CASCADE, related_name="contents")
    section = models.ForeignKey(ContentSection, models.CASCADE, null=True, blank=True)
    nb_col = models.IntegerField(default=2)
    order = models.IntegerField()


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
    display_mode = models.CharField(
        max_length=10,
        choices=[
            ("embedded", "Page intégrée"),
            ("simple", "Lien simple"),
            ("bookmark", "Marque-page"),
        ],
    )


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
