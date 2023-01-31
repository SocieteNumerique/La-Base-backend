from rest_framework import serializers

from main.models import Resource, Evaluation, Criterion
from main.query_changes.permissions import resources_queryset_for_user


class PrimaryKeyResourcesForEvaluations(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        """Limit to resources that we have access to."""
        request = self.context.get("request")
        if not request or request.user.is_anonymous:
            return Resource.objects.none()
        return resources_queryset_for_user(request.user)


class EvaluationSerializer(serializers.ModelSerializer):
    class Meta:
        fields = (
            "comment",
            "criterion",
            "date",
            "id",
            "is_owner",
            "evaluation",
            "resource",
            "user",
            "user_tags",
        )
        model = Evaluation

    date = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()
    resource = PrimaryKeyResourcesForEvaluations()
    user = serializers.StringRelatedField()
    user_tags = serializers.SerializerMethodField()

    def get_date(self, obj: Evaluation):
        return obj.modified.strftime("%d/%m/%Y")

    def get_is_owner(self, obj: Evaluation):
        if not (request := self.context.get("request")):
            return False
        return obj.user == request.user

    def get_user_tags(self, obj: Evaluation):
        return list(obj.user.tags.all().values_list("pk", flat=True))

    def create(self, validated_data):
        request = self.context.get("request")
        if request:
            validated_data["user"] = request.user
        instance, created = Evaluation.objects.update_or_create(
            user=validated_data["user"],
            resource=validated_data["resource"],
            criterion=validated_data["criterion"],
            defaults=dict(
                evaluation=validated_data["evaluation"],
                comment=validated_data["comment"],
            ),
        )
        return instance


class CriterionSerializer(serializers.ModelSerializer):
    class Meta:
        fields = "__all__"
        model = Criterion
