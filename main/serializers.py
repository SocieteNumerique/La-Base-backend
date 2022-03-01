from django.contrib.auth import password_validation
from django.contrib.auth.hashers import make_password
from django.core import exceptions
from rest_framework import serializers
from telescoop_auth.models import User

from main.models import Ressource, Base, Category


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

    def validate_password(self, value):
        errors = None
        try:
            password_validation.validate_password(password=value, user=User)
        except exceptions.ValidationError as e:
            errors = list(e.messages)

        if errors:
            raise serializers.ValidationError(errors)
        return make_password(value)


class BaseRessourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ressource
        abstract = True

    author = AuthSerializer(read_only=True)
    is_short = serializers.ReadOnlyField(default=True)


class ShortRessourceSerializer(BaseRessourceSerializer):
    class Meta(BaseRessourceSerializer.Meta):
        fields = ["id", "title", "is_short"]
        abstract = False

    is_short = serializers.ReadOnlyField(default=True)


class FullRessourceSerializer(BaseRessourceSerializer):
    class Meta(BaseRessourceSerializer.Meta):
        fields = ["id", "title", "author", "content"]
        abstract = False


class BaseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        abstract = True

    base = serializers.PrimaryKeyRelatedField(read_only=True)
    ressources = FullRessourceSerializer(many=True, read_only=True)


class ShortCategorySerializer(BaseCategorySerializer):
    class Meta(BaseCategorySerializer.Meta):
        abstract = False
        fields = ["title", "base", "is_short"]

    is_short = serializers.ReadOnlyField(default=True)


class FullCategorySerializer(BaseCategorySerializer):
    class Meta(BaseCategorySerializer.Meta):
        abstract = False
        fields = ["title", "base", "ressources"]


class BaseBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Base
        abstract = True

    categories = FullCategorySerializer(many=True, read_only=True)
    owner = AuthSerializer()


class ShortBaseSerializer(BaseBaseSerializer):
    class Meta(BaseBaseSerializer.Meta):
        abstract = False
        fields = ["title", "owner", "is_short"]

    is_short = serializers.ReadOnlyField(default=True)


class FullBaseSerializer(BaseBaseSerializer):
    class Meta(BaseBaseSerializer.Meta):
        abstract = False
        fields = ["title", "owner", "categories"]
