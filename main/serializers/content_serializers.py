from rest_framework import serializers

from main.models import (
    LinkContent,
    LinkedResourceContent,
    TextContent,
    ContentBlock,
    Resource,
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
CONTENT_READ_ONLY_FIELDS = ["id", "created", "modified"]
POSSIBLE_CONTENT_TYPES = ["text", "link", "linkedResource"]


class ContentBlockSerializer(serializers.ModelSerializer):
    class Meta:
        fields = content_fields
        read_only_fields = CONTENT_READ_ONLY_FIELDS
        model = ContentBlock


class BaseContentSerializer(serializers.ModelSerializer):
    class Meta:
        fields = content_fields
        read_only_fields = CONTENT_READ_ONLY_FIELDS
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


def get_serializer_by_child_model(block_child_model):
    if block_child_model == "textcontent":
        return TextContentSerializer
    if block_child_model == "linkedresourcecontent":
        return LinkedResourceContentSerializer
    if block_child_model == "linkcontent":
        return LinkContentSerializer


def content_type_to_child_model(content_type):
    return content_type.lower() + "content"


class ReadContentSerializer(serializers.ModelSerializer):
    class Meta:
        fields = content_fields + ["link", "display_mode", "linked_resource_id", "text"]
        read_only_fields = CONTENT_READ_ONLY_FIELDS
        model = ContentBlock

    def to_representation(self, instance: Resource):
        for block_child_model in [
            "textcontent",
            "linkcontent",
            "linkedresourcecontent",
        ]:
            if hasattr(instance, block_child_model):
                serializer = get_serializer_by_child_model(block_child_model)
                sub_content = getattr(instance, block_child_model)
                return serializer(sub_content, context=self.context).data
        raise ValueError("the contentBlock is not typed")


class WriteContentSerializer(serializers.BaseSerializer):
    def to_representation(self, instance):
        if not isinstance(instance, dict):
            raise ValueError("use ReadContentSerializer instead")
        return instance

    @staticmethod
    def get_model_by_type(content_type):
        if content_type == "text":
            return TextContent
        if content_type == "linkedResource":
            return LinkedResourceContent
        if content_type == "link":
            return LinkContent
        raise ValueError("invalid content_type")

    def to_internal_value(self, data):
        if "content_type" not in data:
            raise ValueError("content_type not found and required")

        content_type = data["content_type"]
        data.pop("content_type")
        if content_type not in POSSIBLE_CONTENT_TYPES:
            raise ValueError("invalid content_type")

        block_child_model = content_type_to_child_model(content_type)
        serializer = get_serializer_by_child_model(block_child_model)()
        res = serializer.to_internal_value(data)
        res["content_type"] = content_type
        return res

    def update(self, instance, validated_data):
        # TODO
        pass

    def create(self, validated_data):
        # TODO test
        if "content_type" not in validated_data:
            raise ValueError("content_type not found and required")

        content_type = validated_data["content_type"]
        validated_data.pop("content_type")
        if content_type not in POSSIBLE_CONTENT_TYPES:
            raise ValueError("invalid content_type")

        model = self.get_model_by_type(content_type)
        return model.objects.create(**validated_data)
