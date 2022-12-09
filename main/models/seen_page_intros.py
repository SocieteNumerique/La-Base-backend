from django.db import models

from main.models import User


class SeenIntroSlug(models.Model):
    class Meta:
        unique_together = ("user", "slug")

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    slug = models.CharField(max_length=50)

    def __str__(self):
        return f"seen for slug {self.slug}, user {self.user}"
