from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from main.models import Resource, ContentBlock, ContentSection
from main.serializers.base_resource_serializers import FullResourceSerializer
from main.serializers.content_serializers import (
    ReadContentSerializer,
    WriteContentSerializer,
    ContentOrderSerializer,
    ContentBySectionSerializer,
    ContentSectionSerializer,
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
        serializer = ContentBySectionSerializer(obj)
        return Response(serializer.data)


class ContentView(
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
    mixins.ListModelMixin,
):
    def get_serializer_class(self):
        if self.action in ["retrieve", "list"]:
            return ReadContentSerializer
        return WriteContentSerializer

    @action(detail=False, methods=["PATCH"])
    def order(self, request):
        res_data = []
        for content_id, data in request.data.items():
            content = ContentBlock.objects.get(pk=content_id)
            serializer = ContentOrderSerializer(content, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)

            if getattr(content, "_prefetched_objects_cache", None):
                # If 'prefetch_related' has been applied to a queryset, we need to
                # forcibly invalidate the prefetch cache on the instance.
                content._prefetched_objects_cache = {}

            res_data.append(serializer.data)
        queryset = ContentBlock.objects.filter(id__in=request.data.keys()).all()
        return Response(ContentOrderSerializer(queryset, many=True).data)

    def get_queryset(self):
        return ContentBlock.objects.all()


class SectionView(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
    mixins.RetrieveModelMixin,
):
    def get_queryset(self):
        return ContentSection.objects.all()

    def get_serializer_class(self):
        return ContentSectionSerializer
