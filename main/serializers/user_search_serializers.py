from rest_framework import serializers

from main.models import UserSearch


class UserSearchSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSearch
        fields = [
            "id",
            "data_type",
            "name",
            "query",
        ]

    query = serializers.JSONField()

    def create(self, validated_data):
        user = (request := self.context.get("request", None)) and request.user
        if not user:
            raise ValueError("User must be logged in")

        validated_data["user"] = user
        return super().create(validated_data)
