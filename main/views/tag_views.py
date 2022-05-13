from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from main.models import Tag, TagCategory
from main.serializers.index_serializers import TagSerializer, IndexSerializer


class TagView(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = TagSerializer

    def get_queryset(self):
        return Tag.objects.all()


class TagCategoryView(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = IndexSerializer

    def get_queryset(self):
        return TagCategory.objects.all()

    @action(detail=True, methods=["get"])
    def tags(self, request, pk=None):
        category = TagCategory.objects.get(pk=pk)
        serializer = TagSerializer(category.tags.all(), many=True)
        return Response(serializer.data)
