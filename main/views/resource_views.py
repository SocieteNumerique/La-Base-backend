from rest_framework import mixins, viewsets

from main.models import Resource
from main.serializers.base_resource_serializers import FullResourceSerializer


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
