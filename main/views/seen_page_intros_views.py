from django.http import HttpResponse
from rest_framework import status
from rest_framework.decorators import api_view

from main.models import SeenIntroSlug


@api_view(["GET"])
def mark_intros_seen_for_slugs(request, slugs: str):
    if request.user.is_anonymous:
        return HttpResponse()
    for slug in slugs.split(","):
        _, created = SeenIntroSlug.objects.get_or_create(slug=slug, user=request.user)
    return HttpResponse(status=status.HTTP_200_OK)
