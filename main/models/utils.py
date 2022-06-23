from io import BytesIO

from PIL import Image
from django.core.files.storage import default_storage
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
    memfile = BytesIO()
    img = Image.open(image)
    if img.height > 150 or img.width > 150:
        output_size = (150, 150)
        img.thumbnail(output_size, Image.ANTIALIAS)
        img.save(memfile, img.format)
        default_storage.save(image.name, memfile)
        memfile.close()
        img.close()
