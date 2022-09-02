from hashlib import pbkdf2_hmac

from django.conf import settings
from django.db import models

from main.models import Base, Resource


def hash_ip(ip):
    return pbkdf2_hmac("sha256", ip.encode(), settings.SECRET_KEY.encode(), 100).hex()


class BaseVisit(models.Model):
    class Meta:
        unique_together = ("instance", "date", "ip_hash")

    instance = models.ForeignKey(Base, on_delete=models.CASCADE, related_name="visits")
    date = models.DateField(auto_now=True)
    ip_hash = models.CharField(max_length=64)

    def __str__(self):
        return f"{self.instance.pk} - {self.date} - {self.ip_hash[:8]}"


class ResourceVisit(models.Model):
    class Meta:
        unique_together = ("instance", "date", "ip_hash")

    instance = models.ForeignKey(
        Resource, on_delete=models.CASCADE, related_name="visits"
    )
    date = models.DateField(auto_now=True)
    ip_hash = models.CharField(max_length=64)

    def __str__(self):
        return f"{self.instance.pk} - {self.date} - {self.ip_hash[:8]}"
