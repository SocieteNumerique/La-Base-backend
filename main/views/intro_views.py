from django.db.models import Q
from rest_framework import mixins, viewsets

from main.models import Intro
from main.serializers.intro_serializers import IntroSerializer


class IntroView(
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Intro.objects.filter(~Q(page__startswith="draft")).filter(
        ~Q(slug__startswith="draft")
    )
    serializer_class = IntroSerializer
