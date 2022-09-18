from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.hashers import make_password
from django.core import exceptions
from django.db import IntegrityError
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from main.models.models import Tag
from main.models.user import User
from main.query_changes.utils import query_my_related_tags
from main.user_utils import send_email_confirmation

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
    password = serializers.CharField(write_only=True, required=False, max_length=100)
    is_cnfs = serializers.SerializerMethodField()
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.filter(category__relates_to__contains="User"),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = UserModel
        fields = (
            "id",
            "first_name",
            "last_name",
            "email",
            "password",
            "is_superuser",
            "is_admin",
            "is_staff",
            "is_cnfs",
            "tags",
        )

    @staticmethod
    def get_is_cnfs(obj: User):
        return obj.cnfs_id is not None or obj.cnfs_id_organization is not None

    def create(self, validated_data):
        try:
            user = UserModel.objects.create_user(
                email=validated_data["email"],
                password=validated_data["password"],
                first_name=validated_data["first_name"],
                last_name=validated_data["last_name"],
            )
        except IntegrityError:
            raise ValidationError(
                "un compte existe déjà avec cette adresse mail, veuillez vous connecter"
            )
        try:
            cnfs_tag = Tag.objects.filter(query_my_related_tags("User")).get(
                name=CNFS_RESERVED_TAG_NAME
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

        send_email_confirmation(self.context["request"], user)

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


class UserSerializerForSearch(UserSerializer):
    class Meta(UserSerializer.Meta):
        fields = (
            "id",
            "first_name",
            "last_name",
        )


class NestedUserSerializer(UserSerializerForSearch):
    class Meta(UserSerializerForSearch.Meta):
        extra_kwargs = {"id": {"read_only": False}}


def set_nested_user_fields(instance, validated_data, property_name):
    def find_user_instance(user_data):
        if "id" not in user_data:
            raise ValidationError(f"missing id in {property_name} data")
        return User.objects.get(pk=user_data["id"])

    if property_name in validated_data:
        users = [
            find_user_instance(user_data) for user_data in validated_data[property_name]
        ]
        property_in_instance = getattr(instance, property_name)
        property_in_instance.set(users)
        del validated_data[property_name]
