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


class Ressource(TimeStampedModel):
    title = models.CharField(max_length=100)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.title


class Base(TimeStampedModel):
    title = models.CharField(max_length=100)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.title


class Category(TimeStampedModel):
    class Meta:
        verbose_name = "catégorie"

    title = models.CharField(max_length=100)
    base = models.ForeignKey(Base, on_delete=models.CASCADE, related_name="categories")
    ressources = models.ManyToManyField(Ressource, through="RessourceCategory")

    def __str__(self):
        return self.title


class RessourceCategory(TimeStampedModel):
    class Meta:
        verbose_name = "ressource"

    ressource = models.ForeignKey(Ressource, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
