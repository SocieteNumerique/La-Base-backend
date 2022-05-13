from rest_framework import serializers
from rest_framework.fields import SerializerMethodField

from main.models import TagCategory, Tag


class RecursiveField(serializers.BaseSerializer):
    def to_representation(self, value):
        serializer = self.parent.parent.__class__(value, context=self.context)
        return serializer.data


class BaseTagSerializer(serializers.ModelSerializer):
    class Meta:
        abstract = True
        model = Tag
        fields = "__all__"

    tags = RecursiveField(many=True)


class BaseIndexSerializer(serializers.ModelSerializer):
    class Meta:
        abstract = True
        model = TagCategory
        fields = [
            "id",
            "name",
            "base",
            "is_multi_select",
            "is_draft",
            "accepts_free_tags",
            "tags",
        ]

    tags = SerializerMethodField(method_name="root_tags")


class TagSerializer(BaseTagSerializer):
    class Meta(BaseTagSerializer.Meta):
        abstract = False


class IndexSerializer(BaseIndexSerializer):
    class Meta:
        model = TagCategory
        fields = [
            "id",
            "name",
            "base",
            "is_multi_select",
            "is_draft",
            "accepts_free_tags",
            "tags",
        ]

    tags = SerializerMethodField(method_name="root_tags")

    @staticmethod
    def root_tags(obj: TagCategory):
        return TagSerializer(
            obj.tags.filter(parent_tag_id__isnull=True, is_draft=False), many=True
        ).data


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
