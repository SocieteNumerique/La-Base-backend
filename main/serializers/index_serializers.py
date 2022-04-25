from rest_framework import serializers
from rest_framework.fields import SerializerMethodField

from main.models import TagCategory, Tag


class RecursiveField(serializers.BaseSerializer):
    def to_representation(self, value):
        serializer = self.parent.parent.__class__(value, context=self.context)
        return serializer.data


class TagIndexSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = [
            "id",
            "name",
            "is_free",
            "is_draft",
            "definition",
            "tags",
            "parent_tag",
        ]

    tags = RecursiveField(many=True)


class IndexSerializer(serializers.ModelSerializer):
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
        return TagIndexSerializer(
            obj.tags.filter(parent_tag_id__isnull=True, is_draft=False), many=True
        ).data


class TagIndexAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = [
            "id",
            "name",
            "is_free",
            "is_draft",
            "definition",
            "tags",
            "parent_tag",
        ]

    tags = SerializerMethodField(method_name="no_free_tag_set")

    @staticmethod
    def no_free_tag_set(obj: TagCategory):
        return TagIndexAdminSerializer(obj.tags.filter(is_free=False), many=True).data


class IndexAdminSerializer(serializers.ModelSerializer):
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

    tags = SerializerMethodField(method_name="no_free_root_tags")

    @staticmethod
    def no_free_root_tags(obj: TagCategory):
        return TagIndexAdminSerializer(
            obj.tags.filter(parent_tag_id__isnull=True, is_free=False), many=True
        ).data
