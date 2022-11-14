from django.http import HttpResponse
from rest_framework import status
from rest_framework.decorators import api_view

from main.models import SeenPageIntros


@api_view(["GET"])
def mark_intros_seen_for_page(request, page: str):
    if request.user.is_anonymous:
        return HttpResponse()
    _, created = SeenPageIntros.objects.get_or_create(page=page, user=request.user)
    if created:
        return HttpResponse(status=status.HTTP_201_CREATED)
    return HttpResponse(status=status.HTTP_200_OK)
