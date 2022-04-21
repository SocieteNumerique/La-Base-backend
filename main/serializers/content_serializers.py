from rest_framework import serializers

from main.models import (
    LinkContent,
    LinkedResourceContent,
    TextContent,
    ContentBlock,
)

content_fields = [
    "id",
    "title",
    "annotation",
    "resource_id",
    "parent_folder",
    "created",
    "modified",
    "type",
]
content_read_only_fields = ["id", "created", "modified"]


class ContentBlockSerializer(serializers.ModelSerializer):
    class Meta:
        fields = content_fields
        read_only_fields = content_read_only_fields
        model = ContentBlock


class BaseContentSerializer(serializers.ModelSerializer):
    class Meta:
        fields = content_fields
        read_only_fields = content_read_only_fields
        abstract = True

    type = serializers.SerializerMethodField()

    @staticmethod
    def get_type(obj):
        raise NotImplementedError


class LinkContentSerializer(BaseContentSerializer):
    class Meta(BaseContentSerializer.Meta):
        fields = BaseContentSerializer.Meta.fields + ["link", "display_mode"]
        model = LinkContent

    @staticmethod
    def get_type(obj):
        return "link"


class LinkedResourceContentSerializer(BaseContentSerializer):
    class Meta(BaseContentSerializer.Meta):
        fields = BaseContentSerializer.Meta.fields + ["linked_resource_id"]
        model = LinkedResourceContent

    @staticmethod
    def get_type(obj):
        return "linkedResource"


class TextContentSerializer(BaseContentSerializer):
    class Meta(BaseContentSerializer.Meta):
        fields = BaseContentSerializer.Meta.fields + ["text"]
        model = TextContent

    @staticmethod
    def get_type(obj):
        return "text"


def get_serializer_by_type(content_type):
    if content_type == "textcontent":
        return TextContentSerializer
    if content_type == "linkedresourcecontent":
        return LinkedResourceContentSerializer
    if content_type == "linkcontent":
        return LinkContentSerializer


class ReadContentSerializer(serializers.ModelSerializer):
    class Meta:
        fields = content_fields + ["link", "display_mode", "linked_resource_id", "text"]
        read_only_fields = content_read_only_fields
        model = ContentBlock

    def to_representation(self, instance):
        for content_type in ["textcontent", "linkcontent", "linkedresourcecontent"]:
            if hasattr(instance, content_type):
                serializer = get_serializer_by_type(content_type)
                sub_content = getattr(instance, content_type)
                return serializer(sub_content, context=self.context).data
        return super().to_representation(instance)
