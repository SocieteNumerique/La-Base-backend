from rest_framework import mixins, viewsets

from main.models import Criterion, Evaluation
from main.query_changes.permissions import resources_queryset_for_user
from main.serializers.evaluation_serializers import (
    CriterionSerializer,
    EvaluationSerializer,
)


class EvaluationView(
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Evaluation.objects.all()
    serializer_class = EvaluationSerializer

    def get_object(self):
        # the given pk is actually that of the resource, and the criterion slug
        pk, criterion_slug = self.kwargs["pk"].split("-", 1)
        resource = resources_queryset_for_user(self.request.user).get(pk=pk)
        return Evaluation.objects.get(
            resource=resource, user=self.request.user, criterion=criterion_slug
        )


class CriterionView(
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Criterion.objects.all()
    serializer_class = CriterionSerializer
