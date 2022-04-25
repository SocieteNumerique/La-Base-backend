from django.db.models import Q
from rest_framework import viewsets
from rest_framework.response import Response

from main.models import TagCategory
from main.serializers.index_serializers import IndexSerializer


class IndexView(viewsets.GenericViewSet):
    def get_queryset(self):
        return TagCategory.objects.filter(base_id__isnull=True)

    @staticmethod
    def retrieve(request):
        query = Q()
        if request.GET.get("base"):
            print(request.GET.get("base"))
            query = Q(base_id=request.GET.get("base"))
        index = TagCategory.objects.filter(
            (query | Q(base_id__isnull=True)), is_draft=False
        )
        serializer = IndexSerializer(index, many=True)
        return Response(serializer.data)
