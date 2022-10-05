from rest_framework import mixins, viewsets

from main.models import Page
from main.serializers.page_serializers import ShortPageSerializer, FullPageSerializer


class PageView(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    def get_serializer_class(self):
        if self.action == "list":
            return ShortPageSerializer
        return FullPageSerializer

    def get_queryset(self):
        if self.action == "list":
            return Page.objects.filter(show_in_menu=True)
        return Page.objects.all()
