from django.contrib.auth import password_validation
from django.contrib.auth.hashers import make_password
from django.core import exceptions
from rest_framework import serializers
from telescoop_auth.models import User

from main.models import Resource, Base, ExternalProducer, Tag


class PrimaryKeyTagField(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        return Tag.objects.filter(category__slug="externalProducer_00occupation")


class ExternalProducerSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExternalProducer
        fields = "__all__"

    occupation = PrimaryKeyTagField()


class AuthSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "first_name",
            "last_name",
            "email",
            "is_admin",
        )

    @staticmethod
    def validate_password(self, value):
        errors = None
        try:
            password_validation.validate_password(password=value, user=User)
        except exceptions.ValidationError as e:
            errors = list(e.messages)

        if errors:
            raise serializers.ValidationError(errors)
        return make_password(value)


class PrimaryKeyCreatorField(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        # request = self.context.get('request', None)
        return User.objects.all()


class PrimaryKeyBaseField(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        # request = self.context.get('request', None)
        return Base.objects.all()


class BaseResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resource
        abstract = True

    creator = PrimaryKeyCreatorField(
        default=serializers.CurrentUserDefault(), required=False, allow_null=True
    )

    creator_bases = PrimaryKeyBaseField(required=False, allow_null=True, many=True)
    is_short = serializers.ReadOnlyField(default=True)
    external_producers = ExternalProducerSerializer(many=True)
    # contents = ReadContentSerializer(many=True, required=False)


class ShortResourceSerializer(BaseResourceSerializer):
    class Meta(BaseResourceSerializer.Meta):
        fields = ["id", "title"]
        abstract = False

    is_short = serializers.ReadOnlyField(default=True)


class FullResourceSerializer(BaseResourceSerializer):
    class Meta(BaseResourceSerializer.Meta):
        fields = "__all__"
        abstract = False

    is_short = serializers.ReadOnlyField(default=False)

    def update(self, instance: Resource, validated_data):
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


class BaseBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Base
        abstract = True

    owner = AuthSerializer()


class ShortBaseSerializer(BaseBaseSerializer):
    class Meta(BaseBaseSerializer.Meta):
        abstract = False
        fields = ["id", "title", "owner", "is_short"]

    is_short = serializers.ReadOnlyField(default=True)


class FullBaseSerializer(BaseBaseSerializer):
    class Meta(BaseBaseSerializer.Meta):
        abstract = False
        fields = "__all__"
