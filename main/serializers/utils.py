import base64
import mimetypes
import re
import sys
import uuid

from django.core.files.base import ContentFile
from django.db.models import Q
from django.db.models.fields.files import FieldFile
from rest_framework import serializers
from rest_framework.fields import SkipField
from rest_framework.serializers import ModelSerializer

from main.models import TagCategory, Tag
from main.models.models import LicenseText
from main.models.utils import ResizableImage


class MoreFieldsModelSerializer(ModelSerializer):
    def get_field_names(self, declared_fields, info):
        expanded_fields = super().get_field_names(declared_fields, info)

        if getattr(self.Meta, "extra_fields", None):
            return expanded_fields + self.Meta.extra_fields
        else:
            return expanded_fields


class Base64FileField(serializers.FileField):
    # When the front knows this data among other models properties and PATCHes
    # those other properties, file data is sent to back and should not be interpreted
    # the file should be used only if there is base_64 property
    def validate_empty_values(self, data):
        try:
            if "base_64" not in data and self.context.get("request").method != "GET":
                raise SkipField()
        except TypeError:
            pass
        return super().validate_empty_values(data)

    def to_internal_value(self, data):
        if data is None:
            return None

        if "base_64" in data and isinstance(data["base_64"], str):
            if "data:" in data["base_64"] and ";base64," in data["base_64"]:
                _, file_base64 = data["base_64"].split(";base64,")
            else:
                file_base64 = data["base_64"]

            try:
                decoded_file = base64.b64decode(file_base64)
            except TypeError:
                self.fail("invalid_file")

            file_name_uid = str(uuid.uuid4())[:12]
            complete_file_name = f"{file_name_uid}_{data['name']}"
            res = ContentFile(decoded_file, name=complete_file_name)

            return super().to_internal_value(res)
        if "link" in data and isinstance(data["link"], str):
            return super().to_internal_value(data["link"])
        self.fail("neither 'base64' nor 'link' found in data")

    def to_representation(self, instance: FieldFile):
        if not instance.name:
            return None
        if self.context.get("request"):
            full_link = self.context.get("request").build_absolute_uri(instance.url)
        else:
            full_link = instance.url
        name_without_uuid = re.match("^[^_]*_?(.*)$", instance.name).group(1)
        return {
            "name": name_without_uuid,
            "link": full_link,
            "mime_type": mimetypes.guess_type(instance.name)[0],
        }


class LicenseTextSerializer(serializers.ModelSerializer):
    class Meta:
        model = LicenseText
        fields = ["name", "file", "link", "property_to_use"]

    file = Base64FileField()

    def update(self, instance, validated_data):
        if "link" in validated_data and validated_data["link"] is not None:
            instance.file = None
        if "file" in validated_data and validated_data["file"] is not None:
            instance.link = None
        self.update(instance, validated_data)


class ResizableImageBase64Serializer(serializers.ModelSerializer):
    class Meta:
        model = ResizableImage
        fields = "__all__"
        read_only_fields = [
            "scale_x",
            "scale_y",
            "relative_position_x",
            "relative_position_y",
        ]

    image = Base64FileField()

    @staticmethod
    def apply_coordinates(self, instance, coordinates=None):
        if coordinates is None:
            instance.scale_x = None
            instance.scale_y = None
            instance.relative_position_x = None
            instance.relative_position_y = None
        else:
            instance.scale_x = instance.image.width / coordinates["width"]
            instance.scale_y = instance.image.height / coordinates["height"]
            instance.relative_position_x = coordinates["left"] / coordinates["width"]
            instance.relative_position_y = coordinates["top"] / coordinates["height"]

    def to_internal_value(self, data):
        res = super().to_internal_value(data)
        if "coordinates" in data:
            res["coordinates"] = data["coordinates"]
        return res

    def create(self, validated_data):
        coordinates = (
            validated_data.pop("coordinates")
            if "coordinates" in validated_data
            else None
        )
        instance = super().create(validated_data)
        self.apply_coordinates(instance, coordinates)
        instance.save()
        return instance

    def update(self, instance, validated_data):
        coordinates = (
            validated_data.pop("coordinates")
            if "coordinates" in validated_data
            else None
        )
        has_image_changed = "image" in validated_data
        super().update(instance, validated_data)
        if coordinates or has_image_changed:
            self.apply_coordinates(instance, coordinates)
        instance.save()
        return instance


def create_or_update_resizable_image(
    instance_validated_data, property_name, parent_instance=None
) -> ResizableImage:
    if property_name not in instance_validated_data:
        raise SkipField
    image_data = instance_validated_data.pop(property_name)
    if image_data is None:
        return None

    serializer = ResizableImageBase64Serializer()
    if parent_instance is not None:
        image_instance = getattr(parent_instance, property_name)
        if image_instance:
            return serializer.update(image_instance, image_data)
    return serializer.create(image_data)


SPECIFIC_CATEGORY_SLUGS = {
    "territory": "territory_00city",
    "external_producer": "externalProducer_00occupation",
    "support": "indexation_01RessType",
    "license": "license_01license",
    "needs_account": "license_02needsAccount",
    "price": "license_00price",
}

SPECIFIC_CATEGORY_IDS = {
    "territory": None,
    "external_producer": None,
    "support": None,
    "license": None,
    "needs_account": None,
    "price": None,
}
LICENSE_NEEDS_TEXT_TAG_ID_SET = None


def reset_specific_categories():
    if "migrate" in sys.argv or "backup_db" in sys.argv:
        return
    # before the first time migrations are being done,
    # reset_specific_categories will not work

    global SPECIFIC_CATEGORY_IDS
    global LICENSE_NEEDS_TEXT_TAG_ID_SET

    for category in SPECIFIC_CATEGORY_IDS:
        try:
            SPECIFIC_CATEGORY_IDS[category] = TagCategory.objects.get(
                slug=SPECIFIC_CATEGORY_SLUGS[category]
            ).pk
        except TagCategory.DoesNotExist:
            SPECIFIC_CATEGORY_IDS[category] = None

    LICENSE_NEEDS_TEXT_TAG_ID_SET = set(
        Tag.objects.filter(
            Q(name="Propriétaire") | Q(name="Autre"),
            category_id=SPECIFIC_CATEGORY_IDS["license"],
        ).values_list("pk", flat=True)
    )


reset_specific_categories()
