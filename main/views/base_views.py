from rest_framework import mixins, viewsets

from main.models import Base
from main.serializers.base_resource_serializers import (
    FullBaseSerializer,
    ShortBaseSerializer,
)


class BaseView(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Base.objects.all()

    def get_serializer_class(self):
        if self.kwargs.get("pk"):
            return FullBaseSerializer
        return ShortBaseSerializer
