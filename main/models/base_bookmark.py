from django.db import models

from main.models.models import Base, User
from main.models.utils import TimeStampedModel


class BaseBookmark(TimeStampedModel):
    class Meta:
        unique_together = ("base", "user")

    base = models.ForeignKey(Base, on_delete=models.CASCADE, related_name="bookmarks")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bookmarks")
