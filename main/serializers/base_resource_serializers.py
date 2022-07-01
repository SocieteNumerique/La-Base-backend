from django.db.models import OuterRef, Exists, Q
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from main.models.user import User
from main.query_changes.permissions import (
    resources_queryset_for_user,
    bases_queryset_for_user,
)

from main.query_changes.stats_annotations import resources_queryset_with_stats
from main.serializers.content_serializers import Base64FileField
from main.serializers.custom import MoreFieldsModelSerializer

from main.models.models import Resource, Base, ExternalProducer, Tag, Collection
from main.serializers.user_serializer import (
    AuthSerializer,
    NestedUserSerializer,
    set_nested_user_fields,
)


class PrimaryKeyOccupationTagField(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        return Tag.objects.filter(category__slug="externalProducer_00occupation")


class ExternalProducerSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExternalProducer
        fields = "__all__"

    occupation = PrimaryKeyOccupationTagField()


class PrimaryKeyCreatorField(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        # request = self.context.get('request', None)
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


class BasesPinStatusField(serializers.SerializerMethodField):
    def __init__(self, model, request=None, **kwargs):
        self.model = model
        self.request = request
        super().__init__(**kwargs)

    def to_representation(self, value):
        request = self.request or self.context["request"]
        instance = value
        query_test_root_base = (
            Q(pk=instance.root_base_id)
            if self.model == Resource
            else Q(pk=instance.base_id)
        )
        if request.user.is_anonymous:
            return []
        bases = (
            bases_queryset_for_user(request.user)
            .filter(Q(can_write=True) | Q(can_add_resources=True))
            .annotate(
                is_pinned=(
                    Exists(instance.pinned_in_bases.filter(pk=OuterRef("pk")))
                    | query_test_root_base
                )
            )
        )
        return BaseIsInstancePinnedSerializer(bases, many=True).data


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
            "bases_pinned_in",
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
    bases_pinned_in = BasesPinStatusField(model=Resource)

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
        tags = obj.tags.filter(category__slug="indexation_01RessType").values_list(
            "pk", flat=True
        )
        return tags

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
            "bases_pinned_in",
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
            "bases_pinned_in",
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
        return Resource.objects.filter(root_base=base)


class CollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collection
        fields = ["id", "name", "resources", "base", "bases_pinned_in"]

    resources = PrimaryKeyResourcesForCollectionField(
        many=True, required=False, allow_null=True
    )
    bases_pinned_in = BasesPinStatusField(model=Collection)


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
    profile_image = Base64FileField(required=False, allow_null=True)

    def create(self, validated_data):
        user = self.context["request"].user
        if user.is_anonymous:
            raise ValidationError("Anonymous cannot create a base")
        validated_data["owner"] = user
        return super().create(validated_data)

    def update(self, instance: Base, validated_data):
        set_nested_user_fields(instance, validated_data, "admins")
        set_nested_user_fields(instance, validated_data, "authorized_users")
        set_nested_user_fields(instance, validated_data, "contributors")
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
                user, obj.pinned_resources.prefetch_related("root_base"), full=False
            )
        )
        annotated_qs = resources_queryset_with_stats(
            resources_queryset_for_user(user, obj.resources, full=False)
        )
        return ShortResourceSerializer(
            annotated_qs.union(pinned_resources_qs), many=True, context=self.context
        ).data

    def get_collections(self, obj: Base):
        pinned_collections_qs = obj.pinned_collections.prefetch_related("base")
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
        return obj.tags.filter(
            category__slug="externalProducer_00occupation"
        ).values_list("pk", flat=True)

    @staticmethod
    def get_territory_tags(obj: Base):
        return obj.tags.filter(category__slug="territory_00city").values_list(
            "pk", flat=True
        )


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
            "state",
            "tags",
            "admins",
        ]
