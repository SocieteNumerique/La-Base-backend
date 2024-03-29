from rest_framework import mixins, viewsets

from main.models import Intro
from main.serializers.intro_serializers import IntroSerializer


class IntroView(
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Intro.objects.exclude(slug__startswith="draft")
    serializer_class = IntroSerializer
