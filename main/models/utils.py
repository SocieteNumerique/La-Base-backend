import math
from collections import OrderedDict
from io import BytesIO

from PIL import Image
from django.core.files.storage import default_storage
from django.db import models
from django.db.models import QuerySet
from rest_framework import pagination

from moine_back.settings import RESOURCE_PAGE_SIZE


class TimeStampedModel(models.Model):
    """
    An abstract base class model that provides self-updating
    ``created`` and ``modified`` fields.

    """

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class ResizableImage(models.Model):
    image = models.ImageField()
    # these four values are percentages of the image dimensions
    # scale = complete_size / cropped_size
    # relative_position = position / complete_size
    scale_x = models.DecimalField(null=True, blank=True, max_digits=5, decimal_places=2)
    scale_y = models.DecimalField(null=True, blank=True, max_digits=5, decimal_places=2)
    relative_position_x = models.DecimalField(
        null=True, blank=True, max_digits=5, decimal_places=2
    )
    relative_position_y = models.DecimalField(
        null=True, blank=True, max_digits=5, decimal_places=2
    )


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


class Object(object):
    pass


def paginated_resources_from_qs(qs: QuerySet, page: int):
    from main.serializers.base_resource_serializers import ShortResourceSerializer

    paginator = pagination.PageNumberPagination()
    paginator.page_size = RESOURCE_PAGE_SIZE
    fake_request = Object()
    fake_request.query_params = {"page": page}
    page = paginator.paginate_queryset(qs, fake_request)
    serializer = ShortResourceSerializer(page, many=True)
    return OrderedDict(
        [
            ("count", paginator.page.paginator.count),
            (
                "page_count",
                math.ceil(paginator.page.paginator.count / RESOURCE_PAGE_SIZE),
            ),
            ("results", serializer.data),
        ]
    )
