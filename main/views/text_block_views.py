from rest_framework import mixins, viewsets

from main.models import TextBlock
from main.serializers.text_block_serializers import TextBlockSerializer


class TextBlockView(
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    queryset = TextBlock.objects.all()
    serializer_class = TextBlockSerializer
