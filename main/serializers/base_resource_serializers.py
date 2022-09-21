from django.db.models import Q
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import SkipField

from main.models.models import (
    Resource,
    Base,
    ExternalProducer,
    Tag,
    Collection,
)
from main.query_changes.permissions import resources_queryset_for_user
from main.query_changes.stats_annotations import resources_queryset_with_stats
from main.serializers.pagination import paginated_resources_from_base
from main.serializers.user_serializer import (
    NestedUserSerializer,
    set_nested_user_fields,
    UserSerializerForSearch,
)
from main.serializers.utils import (
    MoreFieldsModelSerializer,
    ResizableImageBase64Serializer,
    create_or_update_resizable_image,
    SPECIFIC_CATEGORY_IDS,
    LicenseTextSerializer,
    get_specific_tags,
    set_nested_license_data,
)


class HasStatsMixin:
    stats = serializers.SerializerMethodField(read_only=True)


class PrimaryKeyOccupationTagField(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        if SPECIFIC_CATEGORY_IDS["external_producer"]:
            return Tag.objects.filter(
                category_id=SPECIFIC_CATEGORY_IDS["external_producer"]
            )
        else:
            return Tag.objects.none()


class ExternalProducerSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExternalProducer
        fields = "__all__"

    occupation = PrimaryKeyOccupationTagField()


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
            "creator",
            "is_labeled",
            "stats",
            "content_stats",
            "support_tags",
            "license_tags",
            "access_price_tags",
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
    profile_image = ResizableImageBase64Serializer(required=False, allow_null=True)
    creator = UserSerializerForSearch(required=False, allow_null=True, read_only=True)
    creator_bases = PrimaryKeyBaseField(required=False, allow_null=True, many=True)
    external_producers = ExternalProducerSerializer(many=True, required=False)
    is_short = serializers.ReadOnlyField(default=True)
    root_base_title = serializers.SerializerMethodField()
    stats = serializers.SerializerMethodField(read_only=True)
    support_tags = serializers.SerializerMethodField()
    pinned_in_bases = serializers.PrimaryKeyRelatedField(
        queryset=Base.objects.all(), many=True, required=False
    )
    license_text = LicenseTextSerializer(required=False, allow_null=True)
    license_tags = serializers.SerializerMethodField()
    access_price_tags = serializers.SerializerMethodField()

    @staticmethod
    def get_can_write(obj: Resource):
        return getattr(obj, "can_write", False)

    @staticmethod
    def get_stats(obj: Resource):
        # TODO actually compute pinned
        res = {"visit_count": getattr(obj, "visit_count", 0), "pinned": None}
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
        return get_specific_tags(obj, ["support"])

    @staticmethod
    def get_license_tags(obj: Resource):
        return get_specific_tags(obj, ["license", "free_license"])

    @staticmethod
    def get_access_price_tags(obj: Resource):
        return get_specific_tags(obj, ["needs_account", "price"])

    def create(self, validated_data):
        try:
            image = create_or_update_resizable_image(validated_data, "profile_image")
            instance = super().create(validated_data)
            instance.profile_image = image
            instance.save()
        except SkipField:
            instance = super().create(validated_data)
        request = self.context.get("request")
        if request:
            instance.creator = request.user
            instance.save()
        instance.can_write = True
        return instance

    def update(self, instance: Resource, validated_data):
        set_nested_user_fields(instance, validated_data, "authorized_users")
        set_nested_license_data(validated_data, instance)
        try:
            image = create_or_update_resizable_image(
                validated_data, "profile_image", instance
            )
            instance.profile_image = image
            instance.save()
        except SkipField:
            pass
        instance = super().update(instance, validated_data)
        if not instance.has_global_license:
            # we forget former global license
            # TODO also copies that license on contents that used it?
            #  if we do that, manage to not have many copies, and not risk deleting common files
            instance.tags.through.objects.filter(
                tag__category_id__in=[
                    SPECIFIC_CATEGORY_IDS["license"],
                    SPECIFIC_CATEGORY_IDS["needs_account"],
                    SPECIFIC_CATEGORY_IDS["price"],
                ]
            ).delete()
            if instance.license_text_id is not None:
                instance.license_text.delete()
                instance.license_text = None
                instance.save()
            instance.contents.update(use_resource_license_and_access=False)
        return instance


class VeryShortResourceSerializer(BaseResourceSerializer):
    class Meta(BaseResourceSerializer.Meta):
        fields = [
            "id",
            "title",
            "is_short",
        ]
        abstract = False

    is_short = serializers.ReadOnlyField(default=True)


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
            "can_write",
            "creator",
            "profile_image",
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
            "license_tags",
            "access_price_tags",
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
        return Resource.objects.filter(
            Q(root_base=base) | Q(pinned_in_bases=base)
        ).distinct()


class BaseCollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collection
        fields = [
            "id",
            "name",
            "description",
            "resources",
            "base",
            "pinned_in_bases",
            "profile_image",
        ]

    resources = serializers.SerializerMethodField()
    pinned_in_bases = serializers.PrimaryKeyRelatedField(
        queryset=Base.objects.all(), many=True, required=False
    )
    profile_image = ResizableImageBase64Serializer(required=False, allow_null=True)

    def get_resources(self, obj: Collection):
        qs = resources_queryset_with_stats(
            resources_queryset_for_user(
                self.context["request"].user,
                obj.resources,
                full=False,
            )
        )
        return ShortResourceSerializer(qs, many=True, context=self.context).data


class ReadCollectionSerializer(BaseCollectionSerializer):
    pass


class UpdateCollectionSerializer(BaseCollectionSerializer):
    resources = PrimaryKeyResourcesForCollectionField(
        many=True, required=False, allow_null=True
    )

    def create(self, validated_data):
        try:
            image = create_or_update_resizable_image(validated_data, "profile_image")
            instance = super().create(validated_data)
            instance.profile_image = image
            instance.save()
        except SkipField:
            instance = super().create(validated_data)
        return instance

    def update(self, instance: Resource, validated_data):
        try:
            image = create_or_update_resizable_image(
                validated_data, "profile_image", instance
            )
            instance.profile_image = image
            instance.save()
        except SkipField:
            pass
        instance = super().update(instance, validated_data)
        return instance


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
            "is_certified",
            "participant_type_tags",
            "territory_tags",
            "profile_image",
            "visit_count",
        ]

    owner = UserSerializerForSearch(required=False, read_only=True)
    admins = NestedUserSerializer(many=True, required=False, allow_null=True)
    authorized_users = NestedUserSerializer(many=True, required=False, allow_null=True)
    authorized_user_tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all(), required=False, allow_null=True
    )
    contributors = NestedUserSerializer(many=True, required=False, allow_null=True)
    resources = serializers.SerializerMethodField()
    resource_choices = serializers.SerializerMethodField()
    can_write = serializers.SerializerMethodField()
    visit_count = serializers.SerializerMethodField()
    can_add_resources = serializers.SerializerMethodField()
    collections = serializers.SerializerMethodField()
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
        try:
            image = create_or_update_resizable_image(validated_data, "profile_image")
            instance = super().create(validated_data)
            instance.profile_image = image
            instance.save()
        except SkipField:
            instance = super().create(validated_data)
        return instance

    def update(self, instance: Base, validated_data):
        set_nested_user_fields(instance, validated_data, "admins")
        set_nested_user_fields(instance, validated_data, "authorized_users")
        set_nested_user_fields(instance, validated_data, "contributors")
        try:
            image = create_or_update_resizable_image(
                validated_data, "profile_image", instance
            )
            instance.profile_image = image
            instance.save()
        except SkipField:
            pass
        return super().update(instance, validated_data)

    @staticmethod
    def get_can_write(obj: Base):
        return getattr(obj, "can_write", False)

    @staticmethod
    def get_visit_count(obj: Base):
        return getattr(obj, "visit_count", 0)

    @staticmethod
    def get_can_add_resources(obj: Base):
        return getattr(obj, "can_add_resources", False)

    def get_resources(self, obj: Base):
        user = self.context["request"].user
        return paginated_resources_from_base(obj, user, 1, context=self.context)

    def get_resource_choices(self, obj: Base):
        user = self.context["request"].user
        return VeryShortResourceSerializer(obj.resources_for_user(user), many=True).data

    def get_collections(self, obj: Base):
        pinned_collections_qs = obj.pinned_collections.prefetch_related("base__pk")
        return ReadCollectionSerializer(
            obj.collections.union(pinned_collections_qs),
            many=True,
            context=self.context,
        ).data

    @staticmethod
    def get_participant_type_tags(obj: Base):
        if SPECIFIC_CATEGORY_IDS["external_producer"]:
            return [
                tag.pk
                for tag in obj.tags.all()
                if tag.category_id == SPECIFIC_CATEGORY_IDS["external_producer"]
            ]
        else:
            return []

    @staticmethod
    def get_territory_tags(obj: Base):
        if SPECIFIC_CATEGORY_IDS["territory"]:
            return [
                tag.pk
                for tag in obj.tags.all()
                if tag.category_id == SPECIFIC_CATEGORY_IDS["territory"]
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
            "resource_choices",
            "collections",
            "contributors",
            "contributor_tags",
            "authorized_users",
            "authorized_user_tags",
            "state",
            "tags",
            "admins",
        ]
