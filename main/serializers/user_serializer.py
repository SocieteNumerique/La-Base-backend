from django.conf.global_settings import AUTHENTICATION_BACKENDS
from django.contrib.auth import get_user_model, password_validation, login
from django.contrib.auth.hashers import make_password
from django.core import exceptions
from rest_framework import serializers

from main.models import Tag

UserModel = get_user_model()
CNFS_RESERVED_TAG_NAME = "Conseiller numérique France Services"
CNFS_EMAIL_DOMAIN = "@conseiller-numerique.fr"


class ChangePasswordSerializer(serializers.Serializer):
    model = UserModel

    """
    Serializer for password change endpoint.
    """
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)


class UserSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(required=True, max_length=100, min_length=2)
    last_name = serializers.CharField(required=True, max_length=100, min_length=2)
    email = serializers.EmailField(required=True, max_length=100)
    password = serializers.CharField(write_only=True, required=True, max_length=100)
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.filter(category__relates_to="User"),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = UserModel
        fields = (
            "first_name",
            "last_name",
            "email",
            "password",
            "is_superuser",
            "is_admin",
            "is_staff",
            "tags",
        )

    def create(self, validated_data):
        user = UserModel.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
        )
        try:
            cnfs_tag = Tag.objects.get(
                name=CNFS_RESERVED_TAG_NAME,
                category__relates_to="User",
            )
        except Tag.DoesNotExist:
            cnfs_tag = None
        tags = validated_data.get("tags", [])
        if cnfs_tag:
            # cnfs tag cannot be set manually
            tags = [tag for tag in tags if tag.pk != cnfs_tag.pk]

        for tag in tags:
            user.tags.add(tag)

        # set cnfs_tag when relevant
        if cnfs_tag and validated_data["email"].endswith(CNFS_EMAIL_DOMAIN):
            user.tags.add(cnfs_tag)

        if self.context.get("request"):
            user.backend = AUTHENTICATION_BACKENDS[0]
            login(self.context.get("request"), user)

        return user

    def validate_password(self, value):
        errors = None
        try:
            password_validation.validate_password(password=value, user=UserModel)
        except exceptions.ValidationError as e:
            errors = {"password": list(e.messages)}

        if errors:
            raise serializers.ValidationError(errors)
        return make_password(value)
