from rest_framework import mixins, viewsets

from main.models import Ressource
from main.serializers import FullRessourceSerializer


class RessourceView(
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = FullRessourceSerializer

    def get_queryset(self):
        return Ressource.objects.all()
