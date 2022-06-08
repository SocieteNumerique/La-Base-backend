from rest_framework import mixins, viewsets

from main.models import Collection
from main.query_changes.permissions import bases_queryset_for_user
from main.serializers.base_resource_serializers import (
    CollectionSerializer,
)


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
