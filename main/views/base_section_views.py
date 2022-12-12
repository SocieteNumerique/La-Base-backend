from django.http import HttpRequest
from rest_framework import mixins, viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response

from main.models.models import BaseSection
from main.query_changes.permissions import bases_queryset_for_user
from main.serializers.base_resource_serializers import BaseSectionSerializer


class BaseSectionHasWriteAccessFilter(filters.BaseFilterBackend):
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
    mixins.DestroyModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    filter_backends = [BaseSectionHasWriteAccessFilter]
    serializer_class = BaseSectionSerializer

    def get_queryset(self):
        return BaseSection.objects.filter(
            base__in=bases_queryset_for_user(self.request.user)
        )

    def perform_create(self, serializer):
        serializer.save(position=self.get_queryset().count())

    @action(detail=False, methods=["PATCH"])
    def sort(self, request):
        base = request.data["base"]
        section_ids = request.data["sections"]
        sections = self.get_queryset().filter(base=base, id__in=section_ids)

        for index, section_id in enumerate(section_ids):
            section = next(
                section_instance
                for section_instance in sections
                if section_instance.id == section_id
            )
            section.position = index
            section.save()

        return Response(section_ids)
