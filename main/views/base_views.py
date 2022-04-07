from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from main.models import Base, TagCategory
from main.serializers.base_resource_serializers import (
    FullBaseSerializer,
    ShortBaseSerializer,
)
from main.serializers.index_serializers import IndexAdminSerializer


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

    @action(detail=True, methods=["get"])
    def index(self, request, pk=None):
        index = TagCategory.objects.filter(base_id=pk)
        serializer = IndexAdminSerializer(index, many=True)
        return Response(serializer.data)
