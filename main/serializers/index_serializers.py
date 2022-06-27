from rest_framework import serializers
from rest_framework.fields import SerializerMethodField

from main.models.models import TagCategory, Tag


class RecursiveField(serializers.BaseSerializer):
    def to_representation(self, value):
        serializer = self.parent.parent.__class__(value, context=self.context)
        return serializer.data


class BaseTagSerializer(serializers.ModelSerializer):
    class Meta:
        abstract = True
        model = Tag
        fields = "__all__"

    # TODO: this creates additional queries and is not used for the moment
    # tags = RecursiveField(many=True, required=False)


class BaseIndexSerializer(serializers.ModelSerializer):
    class Meta:
        abstract = True
        model = TagCategory
        fields = [
            "accepts_free_tags",
            "base",
            "description",
            "id",
            "is_draft",
            "name",
            "maximum_tag_count",
            "relates_to",
            "required_to_be_public",
            "slug",
            "tags",
        ]

    tags = SerializerMethodField(method_name="root_tags")

    @staticmethod
    def root_tags(obj: TagCategory):
        return TagSerializer(
            obj.tags.filter(parent_tag_id__isnull=True, is_draft=False).order_by(
                "name"
            ),
            many=True,
        ).data


class TagSerializer(BaseTagSerializer):
    class Meta(BaseTagSerializer.Meta):
        abstract = False

    count = SerializerMethodField()

    @staticmethod
    def get_count(obj: Tag):
        return getattr(obj, "count", None)


class IndexSerializer(BaseIndexSerializer):
    class Meta(BaseIndexSerializer.Meta):
        abstract = False


class TagIndexAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag

    tags = SerializerMethodField(method_name="no_free_tag_set")

    @staticmethod
    def no_free_tag_set(obj: TagCategory):
        return TagIndexAdminSerializer(obj.tags.filter(is_free=False), many=True).data


class IndexAdminSerializer(BaseIndexSerializer):
    class Meta:
        model = TagCategory
        fields = BaseIndexSerializer.Meta.fields

    tags = SerializerMethodField(method_name="no_free_root_tags")

    @staticmethod
    def no_free_root_tags(obj: TagCategory):
        return TagIndexAdminSerializer(
            obj.tags.filter(parent_tag_id__isnull=True, is_free=False), many=True
        ).data
