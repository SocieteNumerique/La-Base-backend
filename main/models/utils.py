from PIL import Image
from django.db import models


class TimeStampedModel(models.Model):
    """
    An abstract base class model that provides self-updating
    ``created`` and ``modified`` fields.

    """

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


def resize_image(image):
    if not image:
        return
    img = Image.open(image.path)
    if img.height > 150 or img.width > 150:
        output_size = (150, 150)
        img.thumbnail(output_size)
        img.save(image.path)
