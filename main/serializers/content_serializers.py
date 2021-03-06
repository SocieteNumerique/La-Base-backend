from copy import copy

from rest_framework import serializers
from rest_framework.fields import CharField

from main.models.contents import (
    LinkContent,
    LinkedResourceContent,
    TextContent,
    ContentBlock,
    ContentSection,
    FileContent,
)
from main.models.models import Resource
from main.serializers.utils import Base64FileField

content_fields = [
    "id",
    "title",
    "annotation",
    "resource_id",
    "section",
    "created",
    "modified",
    "type",
    "nb_col",
    "order",
]
CONTENT_READ_ONLY_FIELDS = ["id", "created", "modified"]
POSSIBLE_CONTENT_TYPES = ["text", "link", "linkedResource", "file"]

ALLOWED_TAGS = [
    "a",
    "abbr",
    "acronym",
    "b",
    "blockquote",
    "code",
    "em",
    "i",
    "li",
    "ol",
    "strong",
    "ul",
    "h4",
    "h5",
    "h6",
    "p",
]


class ContentOrderSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ["id", "order", "section"]
        model = ContentBlock


class ContentBlockSerializer(serializers.ModelSerializer):
    class Meta:
        fields = "__all__"
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
        fields = BaseContentSerializer.Meta.fields + ["link", "with_preview"]
        model = LinkContent

    @staticmethod
    def get_type(obj):
        return "link"


class LinkedResourceContentSerializer(BaseContentSerializer):
    class Meta(BaseContentSerializer.Meta):
        fields = BaseContentSerializer.Meta.fields + ["linked_resource"]
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

    def to_internal_value(self, data):
        import bleach

        data["text"] = bleach.clean(data["text"], tags=ALLOWED_TAGS)
        return super().to_internal_value(data)


class FileContentSerializer(BaseContentSerializer):
    class Meta(BaseContentSerializer.Meta):
        fields = BaseContentSerializer.Meta.fields + ["file", "with_preview"]
        model = FileContent

    file = Base64FileField(required=False, allow_null=True)

    @staticmethod
    def get_type(obj):
        return "file"


def content_block_instance_to_child_model(content_block):
    for block_child_model in [
        "textcontent",
        "linkcontent",
        "linkedresourcecontent",
        "filecontent",
    ]:
        if hasattr(content_block, block_child_model):
            return block_child_model
    raise ValueError("the contentBlock is not typed")


def get_serializer_by_child_model(block_child_model):
    if block_child_model == "textcontent":
        return TextContentSerializer
    if block_child_model == "linkedresourcecontent":
        return LinkedResourceContentSerializer
    if block_child_model == "linkcontent":
        return LinkContentSerializer
    if block_child_model == "filecontent":
        return FileContentSerializer


def content_type_to_child_model(content_type):
    return content_type.lower() + "content"


class ReadContentSerializer(serializers.ModelSerializer):
    class Meta:
        fields = content_fields + ["link", "with_preview", "linked_resource", "text"]
        read_only_fields = CONTENT_READ_ONLY_FIELDS
        model = ContentBlock

    def to_representation(self, instance: ContentBlock):
        block_child_model = content_block_instance_to_child_model(instance)
        serializer = get_serializer_by_child_model(block_child_model)
        sub_content = getattr(instance, block_child_model)
        return serializer(sub_content, context=self.context).data


class WriteContentSerializer(serializers.BaseSerializer):
    type = CharField()

    def to_representation(self, instance):
        if isinstance(instance, dict):
            return instance
        elif isinstance(instance, ContentBlock):
            return ReadContentSerializer(context=self.context).to_representation(
                instance
            )
        return ReadContentSerializer(context=self.context).to_representation(
            instance.contentblock_ptr
        )

    @staticmethod
    def get_model_by_type(content_type):
        if content_type == "text":
            return TextContent
        if content_type == "linkedResource":
            return LinkedResourceContent
        if content_type == "link":
            return LinkContent
        if content_type == "file":
            return FileContent
        raise ValueError("invalid content_type")

    def to_internal_value(self, data):
        local_data = copy(data)
        if "type" in data:
            local_data.pop("type")

        res = ContentBlockSerializer(partial=True).to_internal_value(local_data)

        # At this point either
        # - there was only generic fields, and we managed all the data
        # - there is still data to me managed, and this data depends on the type of the contant

        for key in res.keys():
            local_data.pop(key)
        if "id" in local_data.keys():
            local_data.pop("id")
        if len(local_data) == 0:
            return res

        # at this point we need to use the appropriate serializer,
        # so we need to know the content's type

        if "type" not in data:
            raise ValueError("type not found and required")

        content_type = data["type"]
        if content_type not in POSSIBLE_CONTENT_TYPES:
            raise ValueError("invalid content_type")

        block_child_model = content_type_to_child_model(content_type)
        child_serializer = get_serializer_by_child_model(block_child_model)(
            partial=True, context=self.context
        )
        res.update(child_serializer.to_internal_value(local_data))
        res["type"] = content_type
        return res

    def update(self, instance, validated_data):
        local_data = copy(validated_data)
        if "type" in local_data:
            local_data.pop("type")
        block = ContentBlockSerializer().update(instance, local_data)

        block_child_model = content_block_instance_to_child_model(instance)
        child_serializer = get_serializer_by_child_model(block_child_model)()

        return child_serializer.update(getattr(block, block_child_model), local_data)

    def create(self, validated_data):
        if "type" not in validated_data:
            raise ValueError("type not found and required")

        content_type = validated_data["type"]
        if content_type not in POSSIBLE_CONTENT_TYPES:
            raise ValueError("invalid content_type")

        local_data = copy(validated_data)
        local_data.pop("type")
        model = self.get_model_by_type(content_type)
        return model.objects.create(**local_data)


# ----------------------- Sections -----------------------


class ContentSectionToNestSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ["id", "title", "is_foldable", "order", "contents"]
        model = ContentSection

    contents = ReadContentSerializer(many=True)


class ContentSectionSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ["id", "title", "is_foldable", "order", "resource"]
        model = ContentSection


class ContentBySectionSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ["sections"]
        model = Resource

    sections = ContentSectionToNestSerializer(many=True)
