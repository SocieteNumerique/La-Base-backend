from django.db import models

from main.models import User


class SeenPageIntros(models.Model):
    class Meta:
        unique_together = ("user", "page")

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    page = models.CharField(max_length=50)

    def __str__(self):
        return f"seen for page {self.page}, user {self.user}"
