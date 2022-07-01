import datetime

from django.db import models
from django.db.models import Count

from main.models.user import User, UserGroup
from main.models.utils import TimeStampedModel, resize_image

RESOURCE_PRODUCER_STATES = [
    ["me", "celui qui ajouté la ressource"],
    ["know", "producteur connu"],
    ["dont-know", "producteur inconnu"],
]
RESOURCE_STATE_CHOICES = [
    ("public", "Public"),
    ("private", "Privé"),
    ("restricted", "Restreint"),
    ("draft", "Brouillon"),
]
RESOURCE_LABEL_CHOICES = [
    ("", "Non demandé"),
    ("pending", "En cours"),
    ("refused", "Refusé"),
    ("accepted", "Accepté"),
]
BASE_CONTACT_STATE_CHOICES = [
    ("public", "Public"),
    ("private", "Privé"),
]


class Base(TimeStampedModel):
    title = models.CharField(max_length=100, verbose_name="titre")
    owner = models.ForeignKey(
        User, models.CASCADE, related_name="owner", verbose_name="propriétaire"
    )
    admins = models.ManyToManyField(
        User, verbose_name="administrateurs", related_name="admins", blank=True
    )
    tags = models.ManyToManyField("Tag", blank=True, related_name="bases")
    # users with these tags will have write access
    contributor_tags = models.ManyToManyField(
        "Tag", blank=True, related_name="contributor_in_bases"
    )
    pinned_resources = models.ManyToManyField(
        "Resource",
        related_name="pinned_in_bases",
        verbose_name="Ressources enregistrées",
        blank=True,
    )
    pinned_collections = models.ManyToManyField(
        "Collection",
        related_name="pinned_in_bases",
        verbose_name="Collections enregistrées",
        blank=True,
    )
    description = models.CharField(max_length=560, null=True, blank=True)
    contact = models.EmailField(null=True, blank=True)
    cover_image = models.ImageField(null=True, blank=True)
    profile_image = models.ImageField(null=True, blank=True)
    state = models.CharField(
        default="draft", choices=RESOURCE_STATE_CHOICES, max_length=10
    )

    contact_state = models.CharField(
        max_length=10,
        verbose_name="Accès au mail",
        choices=BASE_CONTACT_STATE_CHOICES,
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.title

    def save(self, **kwargs):
        super().save(**kwargs)
        resize_image(self.profile_image)


class Collection(TimeStampedModel):
    class Meta:
        unique_together = ("name", "base")

    name = models.CharField(max_length=25, verbose_name="nom")
    base = models.ForeignKey(Base, on_delete=models.CASCADE, related_name="collections")
    resources = models.ManyToManyField(
        "Resource", blank=True, related_name="collections"
    )

    def __str__(self):
        return f"{self.name} - base {self.base.title}"


class TagCategory(TimeStampedModel):
    class Meta:
        unique_together = ("name", "base", "relates_to", "slug")
        ordering = ("slug",)
        verbose_name = "Catégorie de tags"
        verbose_name_plural = "Catégories de tags"

    name = models.CharField(verbose_name="nom", max_length=40)
    slug = models.CharField(
        verbose_name="Slug - à ne pas modifier",
        max_length=40,
        help_text="Convention : familleDeLaCatégorie + _ + ordreÀDeuxChiffresDansLaFamille + slugDeLaCatégorie, ex indexation_03format",
    )
    description = models.CharField(
        verbose_name="description", null=True, max_length=100, blank=True
    )
    required_to_be_public = models.BooleanField(
        verbose_name="remplissage obligatoire pour passer en public", default=False
    )
    maximum_tag_count = models.PositiveSmallIntegerField(
        verbose_name="nombre maximum de tags liés", null=True, blank=True
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
        null=True,
        blank=True,
    )  # can be null, for example for external producer occupation
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
        return self.name


class TagManager(models.Manager):
    def get_queryset(self):
        return Tag.default_manager.all().annotate(count=Count("resources"))


class Tag(TimeStampedModel):
    class Meta:
        ordering = ("name",)
        unique_together = ("name", "category")

    default_manager = models.Manager()
    objects = TagManager()

    name = models.CharField(verbose_name="nom", max_length=60)
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
        return self.name


class Resource(TimeStampedModel):
    class Meta:
        verbose_name = "Ressource"

    title = models.CharField(max_length=100)
    state = models.CharField(
        default="draft", choices=RESOURCE_STATE_CHOICES, max_length=10
    )
    cover_image = models.FileField(null=True, blank=True)
    resource_created_on = models.DateField(default=datetime.date.today)
    creator = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="creator"
    )
    creator_bases = models.ManyToManyField(
        Base,
        verbose_name="Bases qui ont créé la ressource",
        related_name="created_resources",
    )
    root_base = models.ForeignKey(
        Base,
        verbose_name="Base à laquelle la ressource est rattachée",
        on_delete=models.SET_NULL,
        related_name="resources",
        null=True,  # when root_base is null, the resource is "owned" by admins
        blank=True,
    )
    producer_state = models.CharField(
        max_length=10, choices=RESOURCE_PRODUCER_STATES, default="me"
    )
    is_linked_to_a_territory = models.BooleanField(null=True, blank=True)
    access_requires_user_account = models.BooleanField(null=True, blank=True)
    description = models.CharField(
        max_length=560, null=True, blank=True
    )  # only if not in base, first
    zip_code = models.IntegerField(null=True, blank=True)
    url = models.URLField(null=True, blank=True)
    thumbnail = models.ImageField(null=True, blank=True)
    internal_producers = models.ManyToManyField(
        User, blank=True, related_name="internal_producers"
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name="resources")
    label_state = models.CharField(
        max_length=10, default="", blank=True, choices=RESOURCE_LABEL_CHOICES
    )
    label_details = models.TextField(blank=True, null=True)
    groups = models.ManyToManyField(
        "UserGroup", blank=True, through="ResourceUserGroup"
    )
    is_grid_view_enabled = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        """
        Check whether the resource has changed root base,
        if so we remove it from former collections.
        """
        if self.pk and self.root_base != Resource.objects.get(pk=self.pk).root_base:
            for collection in self.collections.all():
                collection.resources.remove(self)
        return super().save(*args, **kwargs)

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

    def is_labeled(self):
        return self.label_state == "accepted"

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
        Resource, models.CASCADE, related_name="external_producers"
    )
    occupation = models.ForeignKey(
        Tag, on_delete=models.SET_NULL, null=True, blank=True
    )

    def __str__(self):
        return f"EXT - ${self.name}"


class ResourceUserGroup(TimeStampedModel):
    """
    We have it in a separate model instead of M2M
    so that we can handle write access.
    """

    resource = models.ForeignKey(
        Resource, on_delete=models.CASCADE, related_name="resource_user_groups"
    )
    group = models.ForeignKey(
        UserGroup, on_delete=models.CASCADE, related_name="resource_user_groups"
    )
    can_write = models.BooleanField(default=False, verbose_name="accès en écriture")
