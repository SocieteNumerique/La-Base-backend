from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from main.models import Resource, ContentBlock
from main.serializers.base_resource_serializers import FullResourceSerializer
from main.serializers.content_serializers import (
    ReadContentSerializer,
    WriteContentSerializer,
)


class ResourceView(
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = FullResourceSerializer

    def get_queryset(self):
        return Resource.objects.all()

    @action(detail=True, methods=["GET"])
    def contents(self, request, pk=None):
        obj: Resource = self.get_object()
        serializer = ReadContentSerializer(obj.contents, many=True)
        return Response(serializer.data)


class ContentView(
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    def get_serializer_class(self):
        if self.action == "retrieve":
            return ReadContentSerializer
        return WriteContentSerializer

    def get_queryset(self):
        return ContentBlock.objects.all()
