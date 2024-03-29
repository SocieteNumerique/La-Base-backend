# Generated by Django 4.0.6 on 2022-10-11 13:35
from decimal import Decimal
from io import BytesIO
from mimetypes import guess_type

from PIL import UnidentifiedImageError
from PIL import Image
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import migrations


class DeleteImage(Exception):
    pass


# noinspection DuplicatedCode
def to_cropped_image(apps, schema_editor):
    ResizableImage = apps.get_model("main", "ResizableImage")
    db_alias = schema_editor.connection.alias
    instances_to_update = []
    errors = []
    for resizable in ResizableImage.objects.using(db_alias).all().iterator():
        resizable.relative_left = float(resizable.relative_position_x or 0)
        resizable.relative_top = float(resizable.relative_position_y or 0)
        resizable.relative_height = (
            1 / float(resizable.scale_y or 1) if resizable.scale_y else 1
        )
        resizable.relative_width = (
            1 / float(resizable.scale_x or 1) if resizable.scale_x else 1
        )

        try:
            create_crop(resizable)
        except DeleteImage:
            resizable.delete()
            continue
        instances_to_update.append(resizable)

    ResizableImage.objects.using(db_alias).bulk_update(
        instances_to_update,
        [
            "relative_left",
            "relative_top",
            "relative_width",
            "relative_height",
            "cropped_image",
            "image",
        ],
    )
    print(errors)


def from_cropped_image(apps, schema_editor):
    ResizableImage = apps.get_model("main", "ResizableImage")
    db_alias = schema_editor.connection.alias
    instances_to_update = []
    for resizable in ResizableImage.objects.using(db_alias).all().iterator():
        resizable.relative_position_x = Decimal.from_float(resizable.relative_left)
        resizable.relative_position_y = Decimal.from_float(resizable.relative_top)
        resizable.scale_y = (
            Decimal.from_float(1 / resizable.relative_height)
            if resizable.relative_height
            else None
        )
        resizable.scale_x = (
            Decimal.from_float(1 / resizable.relative_width)
            if resizable.relative_width
            else None
        )
        instances_to_update.append(resizable)

    ResizableImage.objects.using(db_alias).bulk_update(
        instances_to_update,
        ["relative_position_y", "relative_position_x", "scale_y", "scale_x"],
    )


def create_crop(resizable):
    try:
        img = Image.open(resizable.image.file.file)
    except (ValueError, UnidentifiedImageError, FileNotFoundError):
        raise DeleteImage

    # left, upper, right, and lower
    pil_box = (
        resizable.relative_left * img.width,
        resizable.relative_top * img.height,
        (resizable.relative_left + resizable.relative_width) * img.width,
        (resizable.relative_top + resizable.relative_height) * img.height,
    )

    cropped_img = img.crop(pil_box)
    image_file = BytesIO()
    cropped_img.save(image_file, img.format)

    resizable.cropped_image.save(
        resizable.image.name,
        InMemoryUploadedFile(
            image_file,
            None,
            resizable.image.name,
            guess_type(resizable.image.name)[0],
            cropped_img.size,
            None
        ),
        save=False
    )


class Migration(migrations.Migration):
    dependencies = [
        ('main', '0025_remove_resizableimage_relative_position_x_and_more'),
    ]

    operations = [
        migrations.RunPython(to_cropped_image, from_cropped_image),
    ]
