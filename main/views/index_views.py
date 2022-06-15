from django.db.models import Q, Prefetch
from rest_framework import viewsets
from rest_framework.response import Response

from main.models.models import TagCategory, Tag
from main.serializers.index_serializers import IndexSerializer


class IndexView(viewsets.GenericViewSet):
    def get_queryset(self):
        tags_prefetch = Prefetch("tags", queryset=Tag.objects.all())
        return TagCategory.objects.filter(base_id__isnull=True).prefetch_related(
            tags_prefetch
        )

    def list(self, request):
        qs = self.get_queryset()
        filter_ = Q()
        if request.GET.get("base"):
            print(request.GET.get("base"))
            filter_ = Q(base_id=request.GET.get("base"))
        index = qs.filter((filter_ | Q(base_id__isnull=True)), is_draft=False)
        serializer = IndexSerializer(index, many=True)
        return Response(serializer.data)
