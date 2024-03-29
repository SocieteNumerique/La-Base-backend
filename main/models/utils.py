from functools import partial
from io import BytesIO
from mimetypes import guess_type
from os.path import splitext

import bleach
import rollbar
from PIL import Image
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import models
from versatileimagefield.fields import VersatileImageField
from versatileimagefield.image_warmer import VersatileImageFieldWarmer

from main.constants import ALLOWED_TAGS
from moine_back.settings import VERSATILEIMAGEFIELD_RENDITION_KEY_SETS


class TimeStampedModel(models.Model):
    """
    An abstract base class model that provides self-updating
    ``created`` and ``modified`` fields.

    """

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


def upload_image_location(instance, filename, cropped=False):
    name, ext = splitext(filename)
    return f'{name}{f"_cropped" if cropped else ""}{ext}'


class ResizableImage(models.Model):
    image = VersatileImageField(upload_to=upload_image_location)
    cropped_image = VersatileImageField(
        upload_to=partial(upload_image_location, cropped=True), editable=False
    )

    relative_top = models.FloatField(default=0, blank=True)
    relative_left = models.FloatField(default=0, blank=True)
    relative_height = models.FloatField(default=1, blank=True)
    relative_width = models.FloatField(default=1, blank=True)

    def pil_box(self, width, height):
        (left, upper, right, lower) = (
            self.relative_left * width,
            self.relative_top * height,
            (self.relative_left + self.relative_width) * width,
            (self.relative_top + self.relative_height) * height,
        )
        return left, upper, right, lower

    def create_crop(self):
        # thanks https://stackoverflow.com/a/52936682/14872075
        img = Image.open(self.image.file.file)

        cropped_img = img.crop(self.pil_box(img.width, img.height))
        image_file = BytesIO()
        cropped_img.save(image_file, img.format)
        self.cropped_image.save(
            self.image.name,
            InMemoryUploadedFile(
                image_file,
                None,
                self.image.name,
                guess_type(self.image.name)[0],
                cropped_img.size,
                None,
            ),
            save=False,
        )
        self.cropped_image.delete_all_created_images()

    @property
    def rendition_key(self):
        try:
            return next(
                key_set_name
                for key_set_name in VERSATILEIMAGEFIELD_RENDITION_KEY_SETS.keys()
                if hasattr(self, key_set_name) and getattr(self, key_set_name)
            )
        except StopIteration:
            return ""

    def warm_cropping(self):
        warmer = VersatileImageFieldWarmer(
            instance_or_queryset=self,
            rendition_key_set=self.rendition_key,
            image_attr="cropped_image",
        )
        warmer_full = VersatileImageFieldWarmer(
            instance_or_queryset=self,
            rendition_key_set="cropping_preview",
            image_attr="image",
        )
        _, failed_to_create = warmer.warm()
        _, failed_to_create_full = warmer_full.warm()
        nb_failures = len(failed_to_create_full) + len(failed_to_create)
        if nb_failures > 0:
            rollbar.report_message(
                f"{nb_failures} image crops failed for ResizableImage n° {self.pk}",
                "warning",
            )


class RichText(models.TextField):
    def __init__(self, *args, db_collation=None, **kwargs):
        self.allowed_tags = kwargs.pop("allowed_tags", ALLOWED_TAGS)
        super().__init__(*args, db_collation=db_collation, **kwargs)

    def clean_value(self, value):
        return bleach.clean(value, tags=self.allowed_tags)

    # Update model on save method
    def pre_save(self, model_instance, add):
        value = getattr(model_instance, self.attname)
        if value:
            setattr(model_instance, self.attname, self.clean_value(value))
        return value

    # Update db and allow to clean on update method
    def get_prep_value(self, value):
        if value:
            value = self.clean_value(value)
        return super(RichText, self).get_prep_value(value)
