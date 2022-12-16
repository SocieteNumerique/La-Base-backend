from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from main.models.models import Collection
from main.query_changes.permissions import (
    bases_queryset_for_user,
    resources_queryset_for_user,
)
from main.serializers.base_resource_serializers import (
    ReadCollectionSerializer,
    UpdateCollectionSerializer,
)
from main.views.base_views import generic_pin_action


class CollectionView(
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    def get_serializer_class(self):
        if self.action in ["retrieve", "list"]:
            return ReadCollectionSerializer
        return UpdateCollectionSerializer

    def get_queryset(self):
        return Collection.objects.filter(
            base__in=bases_queryset_for_user(self.request.user)
        )

    @action(detail=True, methods=["PATCH"])
    def resources(self, request, pk=None):
        instance = self.get_object()
        resource = resources_queryset_for_user(request.user).get(
            id=request.data["resource_id"]
        )
        if request.data["action"] == "add":
            instance.resources.add(resource)
        else:
            instance.resources.remove(resource)

        return Response(self.get_serializer_class()(instance).data)

    @action(detail=True, methods=["PATCH"])
    def pin(self, request, pk=None):
        return generic_pin_action(Collection, self, request, pk)
