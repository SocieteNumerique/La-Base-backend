import base64
import mimetypes
import re
import uuid

from django.core.files.base import ContentFile
from django.db.models.fields.files import FieldFile
from rest_framework import serializers
from rest_framework.fields import SkipField
from rest_framework.serializers import ModelSerializer


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
