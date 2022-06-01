from django.http import HttpRequest
from rest_framework import mixins, viewsets, filters
from rest_framework.decorators import action
from rest_framework.permissions import BasePermission
from rest_framework.response import Response

from main.models import Resource, ContentBlock, ContentSection
from main.permissions import resources_queryset_for_user, bases_queryset_for_user
from main.serializers.base_resource_serializers import FullResourceSerializer
from main.serializers.content_serializers import (
    ReadContentSerializer,
    WriteContentSerializer,
    ContentOrderSerializer,
    ContentBySectionSerializer,
    ContentSectionSerializer,
)


class ResourceHasWriteAccessFilter(filters.BaseFilterBackend):
    """
    Filter only writable ressource for user for patch/delete requests.
    """

    def filter_queryset(self, request: HttpRequest, queryset, view):
        if request.method in ["PATCH", "DELETE"]:
            return queryset.filter(can_write=True)

        # GET does not need additional filtering
        return queryset


class UserCanWriteOnBaseForPost(BasePermission):
    def has_permission(self, request, view):
        if request.method != "POST":
            return True

        if (
            bases_queryset_for_user(request.user)
            .filter(can_write=True)
            .filter(pk=request.data["root_base"])
            .exists()
        ):
            return True
        return False


def order_action(model, serializer_class, request):
    res_data = []
    for instance_id, data in request.data.items():
        instance = model.objects.get(pk=instance_id)
        serializer = serializer_class(instance, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        if getattr(instance, "_prefetched_objects_cache", None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        res_data.append(serializer.data)
    queryset = model.objects.filter(id__in=request.data.keys()).all()
    return Response(serializer_class(queryset, many=True).data)


class ResourceView(
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = FullResourceSerializer
    filter_backends = [ResourceHasWriteAccessFilter]
    permission_classes = [UserCanWriteOnBaseForPost]

    def get_queryset(self):
        return resources_queryset_for_user(self.request.user)

    @action(detail=True, methods=["GET"])
    def contents(self, request, pk=None):
        obj: Resource = self.get_object()
        serializer = ContentBySectionSerializer(obj, context={"request": self.request})
        return Response(serializer.data)


class ContentView(
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
    mixins.ListModelMixin,
):
    def get_queryset(self):
        return ContentBlock.objects.filter(
            resource__in=resources_queryset_for_user(self.request.user)
        )

    def get_serializer_context(self):
        context = super(ContentView, self).get_serializer_context()
        context.update({"request": self.request})
        return context

    def get_serializer_class(self):
        if self.action in ["retrieve", "list"]:
            return ReadContentSerializer
        return WriteContentSerializer

    @action(detail=False, methods=["PATCH"])
    def order(self, request):
        return order_action(ContentBlock, ContentOrderSerializer, request)


class SectionView(
    viewsets.GenericViewSet,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
):
    def get_queryset(self):
        return ContentSection.objects.filter(
            resource__in=resources_queryset_for_user(self.request.user)
        )

    def get_serializer_class(self):
        return ContentSectionSerializer

    @action(detail=False, methods=["PATCH"])
    def order(self, request):
        return order_action(ContentSection, ContentSectionSerializer, request)
