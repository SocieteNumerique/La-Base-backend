from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from main.models import Resource
from main.serializers.base_resource_serializers import FullResourceSerializer
from main.serializers.content_serializers import ReadContentSerializer


class ResourceView(
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = FullResourceSerializer
    queryset = Resource.objects.all()

    @action(detail=True, methods=["GET"])
    def contents(self, request, pk=None):
        obj: Resource = self.get_object()
        print(obj.contentblock_set)
        serializer = ReadContentSerializer(obj.contentblock_set, many=True)
        return Response(serializer.data)
