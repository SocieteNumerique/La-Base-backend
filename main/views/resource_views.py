from rest_framework import mixins, viewsets

from main.models import Resource
from main.serializers import FullResourceSerializer


class ResourceView(
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = FullResourceSerializer

    def get_queryset(self):
        return Resource.objects.all()
