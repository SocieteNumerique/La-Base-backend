from django.http import HttpRequest
from rest_framework import mixins, viewsets, filters

from main.models.models import Section
from main.query_changes.permissions import bases_queryset_for_user
from main.serializers.base_resource_serializers import BaseSectionSerializer


class SectionBaseHasWriteAccessFilter(filters.BaseFilterBackend):
    """
    Filter only writable ressource for user for patch/delete requests.
    """

    def filter_queryset(self, request: HttpRequest, queryset, view):
        if request.method in ["PATCH", "DELETE", "PUT"]:
            return queryset.filter(
                base__in=bases_queryset_for_user(request.user).filter(can_write=True)
            )
        return queryset


class BaseSectionView(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    filter_backends = [SectionBaseHasWriteAccessFilter]
    serializer_class = BaseSectionSerializer

    def get_queryset(self):
        return Section.objects.filter(
            base__in=bases_queryset_for_user(self.request.user)
        )

    def perform_create(self, serializer):
        serializer.save(position=self.get_queryset().count())
