from django.contrib.auth import password_validation
from django.contrib.auth.hashers import make_password
from django.core import exceptions
from rest_framework import serializers
from telescoop_auth.models import User

from main.models import Resource, Base
from main.serializers.content_serializers import ReadContentSerializer


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


class BaseResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resource
        abstract = True

    creator = serializers.PrimaryKeyRelatedField(
        read_only=True, default=serializers.CurrentUserDefault()
    )
    is_short = serializers.ReadOnlyField(default=True)
    contents = ReadContentSerializer(many=True, required=False)


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
