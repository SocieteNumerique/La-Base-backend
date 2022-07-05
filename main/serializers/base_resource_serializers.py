from django.db.models import OuterRef, Exists, Q
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from main.models import TagCategory
from main.models.models import Resource, Base, ExternalProducer, Tag, Collection
from main.models.user import User
from main.query_changes.permissions import (
    resources_queryset_for_user,
)
from main.query_changes.stats_annotations import resources_queryset_with_stats
from main.serializers.utils import (
    MoreFieldsModelSerializer,
    Base64FileField,
    ResizableImageBase64Serializer,
    create_or_update_resizable_image,
)

from main.models.models import Resource, Base, ExternalProducer, Tag, Collection
from main.serializers.user_serializer import (
    AuthSerializer,
    NestedUserSerializer,
    set_nested_user_fields,
)

TERRITORY_CATEGORY_ID = None
EXTERNAL_PRODUCER_CATEGORY_ID = None
SUPPORT_CATEGORY_ID = None


def reset_specific_categories():
    global TERRITORY_CATEGORY_ID
    global EXTERNAL_PRODUCER_CATEGORY_ID
    global SUPPORT_CATEGORY_ID

    try:
        TERRITORY_CATEGORY_ID = TagCategory.objects.get(slug="territory_00city").pk
    except TagCategory.DoesNotExist:
        TERRITORY_CATEGORY_ID = None

    try:
        EXTERNAL_PRODUCER_CATEGORY_ID = TagCategory.objects.get(
            slug="externalProducer_00occupation"
        ).pk
    except TagCategory.DoesNotExist:
        SUPPORT_CATEGORY_ID = None
    try:
        SUPPORT_CATEGORY_ID = TagCategory.objects.get(slug="indexation_01RessType").pk
    except TagCategory.DoesNotExist:
        SUPPORT_CATEGORY_ID = None


reset_specific_categories()


class PrimaryKeyOccupationTagField(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        if EXTERNAL_PRODUCER_CATEGORY_ID:
            return Tag.objects.filter(category=EXTERNAL_PRODUCER_CATEGORY_ID)
        else:
            return Tag.objects.none()


class ExternalProducerSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExternalProducer
        fields = "__all__"

    occupation = PrimaryKeyOccupationTagField()


class PrimaryKeyCreatorField(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        request = self.context.get("request", None)
        if request:
            return User.objects.filter(pk=request.user.pk)
        return User.objects.all()


class PrimaryKeyBaseField(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        # request = self.context.get('request', None)
        return Base.objects.all()


class BaseIsInstancePinnedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Base
        fields = ["id", "is_pinned"]

    is_pinned = serializers.SerializerMethodField()

    @staticmethod
    def get_is_pinned(obj: Base):
        return getattr(obj, "is_pinned", False)


class BaseResourceSerializer(MoreFieldsModelSerializer):
    class Meta:
        model = Resource
        abstract = True
        read_only_fields = [
            "is_labeled",
            "stats",
            "content_stats",
            "support_tags",
            "can_write",
            "label_state",
            "label_details",
        ]

    authorized_users = NestedUserSerializer(many=True, required=False, allow_null=True)
    authorized_user_tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all(), required=False, allow_null=True
    )
    can_write = serializers.SerializerMethodField()
    content_stats = serializers.SerializerMethodField(read_only=True)
    contributors = NestedUserSerializer(many=True, required=False, allow_null=True)
    cover_image = Base64FileField(required=False, allow_null=True)
    creator = PrimaryKeyCreatorField(
        default=serializers.CurrentUserDefault(), required=False, allow_null=True
    )
    creator_bases = PrimaryKeyBaseField(required=False, allow_null=True, many=True)
    external_producers = ExternalProducerSerializer(many=True, required=False)
    is_short = serializers.ReadOnlyField(default=True)
    root_base_title = serializers.SerializerMethodField()
    stats = serializers.SerializerMethodField(read_only=True)
    support_tags = serializers.SerializerMethodField()
    pinned_in_bases = serializers.PrimaryKeyRelatedField(
        queryset=Base.objects.all(), many=True, required=False
    )

    @staticmethod
    def get_can_write(obj: Resource):
        return getattr(obj, "can_write", False)

    @staticmethod
    def get_stats(obj: Resource):
        # TODO actually save / compute that
        res = {"views": None, "pinned": None}
        return res

    @staticmethod
    def get_content_stats(obj: Resource):
        return {
            "files": getattr(obj, "nb_files", None),
            "links": getattr(obj, "nb_links", None),
        }

    @staticmethod
    def get_root_base_title(obj: Resource):
        if not obj.root_base:
            return None
        return obj.root_base.title

    @staticmethod
    def get_support_tags(obj: Resource):
        if SUPPORT_CATEGORY_ID:
            if "tags" in obj._prefetched_objects_cache:
                return [
                    tag.pk
                    for tag in obj.tags.all()
                    if tag.category_id == SUPPORT_CATEGORY_ID
                ]
            else:
                return obj.tags.filter(
                    category__slug="indexation_01RessType"
                ).values_list("pk", flat=True)
        else:
            return []

    def create(self, validated_data):
        instance = super().create(validated_data)
        instance.can_write = True
        return instance

    def update(self, instance, validated_data):
        set_nested_user_fields(instance, validated_data, "authorized_users")
        return super().update(instance, validated_data)


class ShortResourceSerializer(BaseResourceSerializer):
    class Meta(BaseResourceSerializer.Meta):
        fields = [
            "id",
            "title",
            "is_short",
            "description",
            "is_labeled",
            "stats",
            "content_stats",
            "support_tags",
            "root_base",
            "root_base_title",
            "pinned_in_bases",
        ]
        abstract = False

    is_short = serializers.ReadOnlyField(default=True)


class FullResourceSerializer(BaseResourceSerializer):
    class Meta(BaseResourceSerializer.Meta):
        fields = "__all__"
        extra_fields = [
            "is_labeled",
            "stats",
            "content_stats",
            "support_tags",
            "can_write",
            "pinned_in_bases",
        ]
        abstract = False

    is_short = serializers.ReadOnlyField(default=False)

    def update(self, instance: Resource, validated_data):
        """
        Handle external producers
        """
        if "external_producers" in validated_data:
            ext_producers = validated_data.pop("external_producers")
            new_producers = []
            for producer in ext_producers:
                email_contact = producer.pop("email_contact")
                producer["resource"] = instance
                new_producer, _ = ExternalProducer.objects.update_or_create(
                    email_contact=email_contact,
                    defaults=producer,
                )
                new_producers.append(new_producer)

            new_producers_ids = {producer.pk for producer in new_producers}
            # remove old producers
            for producer in instance.external_producers.all():
                if producer.pk not in new_producers_ids:
                    producer.delete()
        return super().update(instance, validated_data)

    @staticmethod
    def get_contents(obj):
        pass


class PrimaryKeyResourcesForCollectionField(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        """Limit to resource that are linked to the base the collection belongs to."""
        request = self.context["request"]
        if "pk" in request.parser_context["kwargs"]:
            collection_pk = request.parser_context["kwargs"]["pk"]
            collection = Collection.objects.get(pk=collection_pk)
            base = collection.base
        elif "base" in request.data:
            base = Base.objects.get(pk=request.data["base"])
        return Resource.objects.filter(Q(root_base=base) | Q(pinned_in_bases=base))


class CollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collection
        fields = ["id", "name", "resources", "base", "pinned_in_bases"]

    resources = PrimaryKeyResourcesForCollectionField(
        many=True, required=False, allow_null=True
    )
    pinned_in_bases = serializers.PrimaryKeyRelatedField(
        queryset=Base.objects.all(), many=True, required=False
    )


class BaseBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Base
        abstract = True
        fields = [
            "id",
            "title",
            "owner",
            "can_write",
            "can_add_resources",
            "participant_type_tags",
            "territory_tags",
            "profile_image",
        ]

    owner = AuthSerializer(required=False, read_only=True)
    admins = NestedUserSerializer(many=True, required=False, allow_null=True)
    authorized_users = NestedUserSerializer(many=True, required=False, allow_null=True)
    authorized_user_tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all(), required=False, allow_null=True
    )
    contributors = NestedUserSerializer(many=True, required=False, allow_null=True)
    resources = serializers.SerializerMethodField()
    can_write = serializers.SerializerMethodField()
    can_add_resources = serializers.SerializerMethodField()
    collections = serializers.SerializerMethodField()
    resources_in_pinned_collections = serializers.SerializerMethodField()
    contributor_tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all(), required=False, allow_null=True
    )
    participant_type_tags = serializers.SerializerMethodField()
    territory_tags = serializers.SerializerMethodField()
    profile_image = ResizableImageBase64Serializer(required=False, allow_null=True)

    def create(self, validated_data):
        user = self.context["request"].user
        if user.is_anonymous:
            raise ValidationError("Anonymous cannot create a base")
        validated_data["owner"] = user
        instance = super().create(validated_data)
        create_or_update_resizable_image(instance, validated_data, "profile_image")
        return instance

    def update(self, instance: Base, validated_data):
        set_nested_user_fields(instance, validated_data, "admins")
        set_nested_user_fields(instance, validated_data, "authorized_users")
        set_nested_user_fields(instance, validated_data, "contributors")
        create_or_update_resizable_image(instance, validated_data, "profile_image")
        return super().update(instance, validated_data)

    @staticmethod
    def get_can_write(obj: Base):
        return getattr(obj, "can_write", False)

    @staticmethod
    def get_can_add_resources(obj: Base):
        return getattr(obj, "can_add_resources", False)

    def get_resources(self, obj: Base):
        user = self.context["request"].user
        pinned_resources_qs = resources_queryset_with_stats(
            resources_queryset_for_user(
                user, obj.pinned_resources.prefetch_related("root_base__pk"), full=False
            )
        )
        annotated_qs = resources_queryset_with_stats(
            resources_queryset_for_user(user, obj.resources, full=False)
        )
        return ShortResourceSerializer(
            annotated_qs.union(pinned_resources_qs), many=True, context=self.context
        ).data

    def get_collections(self, obj: Base):
        pinned_collections_qs = obj.pinned_collections.prefetch_related("base__pk")
        return CollectionSerializer(
            obj.collections.union(pinned_collections_qs),
            many=True,
            context=self.context,
        ).data

    def get_resources_in_pinned_collections(self, obj: Base):
        user = self.context["request"].user
        qs = resources_queryset_with_stats(
            resources_queryset_for_user(user, full=False)
            .exclude(root_base=obj)
            .filter(
                Exists(obj.pinned_collections.filter(id__in=OuterRef("collections")))
            )
        )
        return ShortResourceSerializer(qs, many=True, context=self.context).data

    @staticmethod
    def get_participant_type_tags(obj: Base):
        if EXTERNAL_PRODUCER_CATEGORY_ID:
            return [
                tag.pk
                for tag in obj.tags.all()
                if tag.category_id == EXTERNAL_PRODUCER_CATEGORY_ID
            ]
        else:
            return []

    @staticmethod
    def get_territory_tags(obj: Base):
        if TERRITORY_CATEGORY_ID:
            return [
                tag.pk
                for tag in obj.tags.all()
                if tag.category_id == TERRITORY_CATEGORY_ID
            ]
        else:
            return []


class ShortBaseSerializer(BaseBaseSerializer):
    class Meta(BaseBaseSerializer.Meta):
        abstract = False
        fields = BaseBaseSerializer.Meta.fields + ["is_short"]

    is_short = serializers.ReadOnlyField(default=True)


class FullBaseSerializer(BaseBaseSerializer):
    class Meta(BaseBaseSerializer.Meta):
        abstract = False
        fields = BaseBaseSerializer.Meta.fields + [
            "contact",
            "description",
            "resources",
            "collections",
            "resources_in_pinned_collections",
            "contributors",
            "contributor_tags",
            "authorized_users",
            "authorized_user_tags",
            "state",
            "tags",
            "admins",
        ]
