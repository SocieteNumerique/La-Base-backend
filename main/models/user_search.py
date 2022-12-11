from django.db import models

from main.models import User


class UserSearch(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    query = models.TextField()
