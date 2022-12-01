from django.db.models import Q
from django.http import HttpRequest
from rest_framework import mixins, viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.permissions import BasePermission
from rest_framework.response import Response

from main.models.models import Resource
from main.models.contents import ContentBlock, ContentSection
from main.query_changes.permissions import (
    resources_queryset_for_user,
    bases_queryset_for_user,
)
from main.query_changes.stats_annotations import resources_queryset_with_stats
from main.serializers.base_resource_serializers import (
    FullResourceSerializer,
    ShortResourceSerializer,
    DuplicateAnswerResourceSerializer,
)
from main.serializers.content_serializers import (
    ReadContentSerializer,
    WriteContentSerializer,
    ContentOrderSerializer,
    ContentBySectionSerializer,
    ContentSectionSerializer,
)
from main.views.base_views import generic_pin_action
from moine_back import settings


class ResourceHasWriteAccessFilter(filters.BaseFilterBackend):
    """
    Filter only writable ressource for user for patch/delete requests.
    """

    def filter_queryset(self, request: HttpRequest, queryset, view):
        if request.method in ["PATCH", "DELETE", "PUT"]:
            return queryset.filter(can_write=True)

        # GET does not need additional filtering
        return queryset


class UserCanWriteOnBaseForPost(BasePermission):
    def has_permission(self, request, view):
        if request.method != "POST" or not request.data:
            return True

        return (
            bases_queryset_for_user(request.user)
            .filter(can_add_resources=True)
            .filter(pk=request.data["root_base"])
            .exists()
        )


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

    duplicate_key_param = "__trigram_similar" if settings.IS_POSTGRESQL_DB else ""

    def get_queryset(self):
        return resources_queryset_with_stats(
            resources_queryset_for_user(self.request.user)
        )

    @action(detail=True, methods=["GET"])
    def contents(self, request, pk=None):
        # TODO optimize queryset to avoid later content tags requests:
        #  prefetch("contents__tags") doesn't help
        obj: Resource = self.get_object()
        serializer = ContentBySectionSerializer(
            obj, context=self.get_serializer_context()
        )
        return Response(serializer.data)

    @action(detail=True, methods=["GET"])
    def short(self, request, pk=None):
        instance = self.get_object()
        serializer = ShortResourceSerializer(
            instance, context=self.get_serializer_context()
        )
        return Response(serializer.data)

    @action(detail=True, methods=["PATCH"])
    def pin(self, request, pk=None):
        return generic_pin_action(Resource, self, request, pk)

    @action(detail=True, methods=["GET"])
    def duplicate(self, request, pk):
        resource_title = request.query_params.get("title", "")
        resource_description = request.query_params.get("description", "")
        instance = self.get_object()
        excluded_resource = [
            pk,
            *instance.ignored_duplicates.values_list("id", flat=True),
            *instance.confirmed_duplicates.values_list("id", flat=True),
        ]
        queryset_resources = self.get_queryset()
        queryset_resources = queryset_resources.exclude(
            id__in=excluded_resource
        ).filter(
            Q(**{f"title{self.duplicate_key_param}": resource_title})
            | Q(**{f"description{self.duplicate_key_param}": resource_description})
        )
        return Response(queryset_resources.values_list("id", flat=True))

    @action(detail=True, methods=["PATCH"])
    def duplicate_answers(self, request, pk):
        resource = self.get_object()
        serializer = DuplicateAnswerResourceSerializer(resource, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

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

    def create(self, request, *args, **kwargs):
        is_many = isinstance(request.data, list)
        serializer = self.get_serializer(data=request.data, many=is_many)
        # from here it is the package's function
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

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
