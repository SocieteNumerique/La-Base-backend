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


#     TODO autorisations


class TagCategory(TimeStampedModel):
    class Meta:
        unique_together = ("name", "base")
        verbose_name = "Catégorie de tags"
        verbose_name_plural = "Catégories de tags"

    name = models.CharField(max_length=20)
    base = models.ForeignKey(Base, models.CASCADE, null=True, blank=True)
    relates_to = models.CharField(
        max_length=10,
        choices=[("Resource", "Ressource"), ("User", "Utilisateur"), ("Base", "Base")],
    )


class Tag(TimeStampedModel):
    class Meta:
        unique_together = ("name", "category")

    name = models.CharField(max_length=20)
    category = models.ForeignKey(TagCategory, on_delete=models.CASCADE)
    parent_tag = models.ForeignKey("self", models.CASCADE, null=True, blank=True)


class Resource(TimeStampedModel):
    class Meta:
        verbose_name = "Ressource"

    title = models.CharField(max_length=100)
    content = models.TextField()
    creator = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="creator"
    )
    root_base = models.ForeignKey(Base, on_delete=models.PROTECT)
    is_draft = models.BooleanField(default=True)
    description = models.CharField(max_length=60)
    zip_code = models.IntegerField(null=True, blank=True)
    url = models.URLField(null=True, blank=True)
    thumbnail = models.ImageField(null=True, blank=True)
    linked_resources = models.ManyToManyField("self", null=True, blank=True)
    internal_producer = models.ManyToManyField(
        User, related_name="internal_producers", null=True, blank=True
    )
    # category : is it dependant of the base ?
    # tags

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
