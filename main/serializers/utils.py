import base64
import mimetypes
import re
import sys
import uuid

from django.core.files.base import ContentFile
from django.db import OperationalError
from django.db.models import Q
from django.db.models.fields.files import FieldFile
from rest_framework import serializers
from rest_framework.fields import SkipField
from rest_framework.serializers import ModelSerializer

from main.models import TagCategory, Tag
from main.models.models import LicenseText
from main.models.utils import ResizableImage


def create_or_update_nested_object(
    instance_validated_data, property_name, serializer, parent_instance=None
):
    if property_name not in instance_validated_data:
        raise SkipField
    child_data = instance_validated_data.pop(property_name)
    if child_data is None:
        return None

    serializer = serializer()
    if parent_instance is not None:
        child_instance = getattr(parent_instance, property_name)
        if child_instance:
            return serializer.update(child_instance, child_data)
    child_instance = serializer.create(child_data)
    child_instance.save()
    return child_instance


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
        fields = ["id", "file", "link", "name"]

    file = Base64FileField(allow_null=True, required=True)


def create_or_update_license_text(
    instance_validated_data, property_name, parent_instance=None
) -> LicenseText:
    return create_or_update_nested_object(
        instance_validated_data, property_name, LicenseTextSerializer, parent_instance
    )


def set_nested_license_data(validated_data, instance):  # noqa: C901
    def remove_free():
        free_license_tags = Tag.objects.filter(
            category_id=SPECIFIC_CATEGORY_IDS["free_license"]
        ).values_list("pk", flat=True)
        instance.tags.through.objects.filter(tag_id__in=free_license_tags).delete()
        if "tags" in validated_data:
            validated_data["tags"] = [
                t for t in validated_data["tags"] if t.pk not in free_license_tags
            ]

    def remove_license_text():
        if instance.license_text_id is not None:
            instance.license_text.delete()
            validated_data["license_text"] = None

    def remove_license_text_name():
        test_proprietary = (
            len(
                [
                    tag.pk
                    for tag in validated_data["tags"]
                    if tag.category_id == SPECIFIC_CATEGORY_IDS["license"]
                    and tag.slug == "main_01proprietary"
                ]
            )
            > 0
        )
        if not test_proprietary:
            return
        try:
            instance.license_text.name = ""
            instance.license_text.save()
        except AttributeError:
            pass

        try:
            validated_data["license_text"]["name"] = ""
        except KeyError:
            pass

    try:
        license_text = create_or_update_license_text(
            validated_data, "license_text", instance
        )
        instance.license_text = license_text
        instance.save()
    except SkipField:
        pass

    if "tags" not in validated_data:
        return

    test_license_data = len(
        [
            tag.pk
            for tag in validated_data["tags"]
            if tag.category_id == SPECIFIC_CATEGORY_IDS["license"]
        ]
    )
    test_license_needs_text = LICENSE_NEEDS_TEXT_TAG_ID_SET.intersection(
        [tag.pk for tag in validated_data["tags"]]
    )

    if not test_license_data:
        remove_license_text()
        remove_free()
        return
    if test_license_needs_text:
        remove_free()
        remove_license_text_name()
    else:
        remove_license_text()


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
    def apply_coordinates(instance, coordinates=None):
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
    return create_or_update_nested_object(
        instance_validated_data,
        property_name,
        ResizableImageBase64Serializer,
        parent_instance,
    )


SPECIFIC_CATEGORY_SLUGS = {
    "territory": "territory_00city",
    "external_producer": "externalProducer_00occupation",
    "support": "indexation_01RessType",
    "license": "license_01license",
    "free_license": "license_02free",
    "needs_account": "license_04access",
    "price": "license_00price",
    "participant": "general_00participantType",
}

SPECIFIC_CATEGORY_IDS = {
    "territory": None,
    "external_producer": None,
    "support": None,
    "license": None,
    "free_license": None,
    "needs_account": None,
    "price": None,
    "participant": None,
}
LICENSE_NEEDS_TEXT_TAG_ID_SET = set()


def reset_specific_categories():
    if "migrate" in sys.argv or "backup_db" in sys.argv:
        return
    # before the first time migrations are being done,
    # reset_specific_categories will not work

    global SPECIFIC_CATEGORY_IDS
    global LICENSE_NEEDS_TEXT_TAG_ID_SET

    try:
        for category in SPECIFIC_CATEGORY_IDS:
            try:
                SPECIFIC_CATEGORY_IDS[category] = TagCategory.objects.get(
                    slug=SPECIFIC_CATEGORY_SLUGS[category]
                ).pk
            except TagCategory.DoesNotExist:
                SPECIFIC_CATEGORY_IDS[category] = None

        LICENSE_NEEDS_TEXT_TAG_ID_SET = set(
            Tag.objects.filter(
                Q(slug="main_01proprietary") | Q(slug="main_02other"),
                category_id=SPECIFIC_CATEGORY_IDS["license"],
            ).values_list("pk", flat=True)
        )
    except OperationalError:
        pass


def get_specific_tags(obj, categories):
    res = []
    access_tag_category_slugs = [
        SPECIFIC_CATEGORY_SLUGS[tag_category] for tag_category in categories
    ]

    if "tags" in getattr(obj, "_prefetched_objects_cache", []):
        # TODO actually prefetch in parent serializer
        for tag_category in categories:
            if SPECIFIC_CATEGORY_IDS[tag_category]:
                res += [
                    tag.pk
                    for tag in obj.tags.all()
                    if tag.category_id == SPECIFIC_CATEGORY_IDS[tag_category]
                ]
    else:
        res += obj.tags.filter(
            category__slug__in=access_tag_category_slugs
        ).values_list("pk", flat=True)
    return res


reset_specific_categories()
