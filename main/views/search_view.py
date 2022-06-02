from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.request import Request

from main.search import search_resources, search_bases
from main.serializers.base_resource_serializers import (
    ShortResourceSerializer,
    ShortBaseSerializer,
)


@api_view(["POST"])
def search(request: Request, data_type):
    text = request.data.get("text", "")
    if data_type == "resources":
        serializer = ShortResourceSerializer
        search_function = search_resources
    else:
        serializer = ShortBaseSerializer
        search_function = search_bases
    data = serializer(many=True).to_representation(
        search_function(request.user, text=text)
    )
    return JsonResponse({"data_type": data_type, "objects": data})
