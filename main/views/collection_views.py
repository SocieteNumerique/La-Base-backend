from rest_framework import mixins, viewsets
from rest_framework.decorators import action

from main.models.models import Collection
from main.query_changes.permissions import bases_queryset_for_user
from main.serializers.base_resource_serializers import CollectionSerializer
from main.views.base_views import generic_pin_action


class CollectionView(
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = CollectionSerializer

    def get_queryset(self):
        return Collection.objects.filter(
            base__in=bases_queryset_for_user(self.request.user)
        )

    @action(detail=True, methods=["PATCH"])
    def pin(self, request, pk=None):
        return generic_pin_action(Collection, self, request, pk)
