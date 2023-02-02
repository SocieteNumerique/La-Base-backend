from django.db import models

from main.models.user import User

DATA_TYPE_CHOICES = [
    ("resources", "ressources"),
    ("bases", "bases"),
]


class UserSearch(models.Model):
    data_type = models.CharField(max_length=9, choices=DATA_TYPE_CHOICES)
    name = models.CharField(max_length=30)
    query = models.JSONField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
