from django.http import HttpRequest
from rest_framework import mixins, viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response

from main.models.models import TagCategory
from main.query_changes.permissions import bases_queryset_for_user
from main.serializers.base_resource_serializers import (
    FullBaseSerializer,
    ShortBaseSerializer,
    BasesPinStatusField,
)
from main.serializers.index_serializers import IndexAdminSerializer


class BaseHasWriteAccessFilter(filters.BaseFilterBackend):
    """
    Filter only writable ressource for user for patch/delete requests.
    """

    def filter_queryset(self, request: HttpRequest, queryset, view):
        if request.method in ["PATCH", "DELETE"]:
            return queryset.filter(can_write=True)

        # GET does not need additional filtering
        return queryset


class BaseView(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    filter_backends = [BaseHasWriteAccessFilter]

    def get_queryset(self):
        return bases_queryset_for_user(self.request.user)

    def get_serializer_class(self):
        if self.kwargs.get("pk"):
            return FullBaseSerializer
        return ShortBaseSerializer

    @action(detail=True, methods=["get"])
    def index(self, request, pk=None):
        index = TagCategory.objects.filter(base_id=pk)
        serializer = IndexAdminSerializer(index, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def short(self, request, pk=None):
        instance = self.get_object()
        serializer = ShortBaseSerializer(
            instance, context=self.get_serializer_context()
        )
        return Response(serializer.data)


def generic_pin_action(model, self, request, pk=None):
    model_name = model._meta.model_name  # _meta is not actually protected
    instance: model = self.get_queryset().distinct().get(pk=pk)
    if self.request.method == "PATCH":
        base = (
            bases_queryset_for_user(request.user)
            .filter(can_write=True)
            .distinct()
            .get(pk=request.data["id"])
        )
        if request.data["is_pinned"]:
            getattr(base, f"pinned_{model_name}s").add(instance)
        else:
            getattr(base, f"pinned_{model_name}s").remove(instance)
        base.save()
    return Response(
        BasesPinStatusField(model=model, request=request).to_representation(instance)
    )
