from rest_framework.decorators import api_view
from rest_framework.exceptions import APIException
from rest_framework.request import Request
from rest_framework.response import Response
from telescoop_auth.serializers import AuthSerializer

from main.search import search_resources, search_bases, search_users
from main.serializers.base_resource_serializers import (
    ShortResourceSerializer,
    ShortBaseSerializer,
)


class UserSerializerForSearch(AuthSerializer):
    class Meta(AuthSerializer.Meta):
        fields = (
            "id",
            "first_name",
            "last_name",
        )


class HideEmailUserSerializer(AuthSerializer):
    class Meta(AuthSerializer.Meta):
        fields = (field for field in AuthSerializer.Meta.fields if field != "email")


@api_view(["POST"])
def search(request: Request, data_type):
    text = request.data.get("text", "")
    if data_type == "resources":
        serializer = ShortResourceSerializer
        search_function = search_resources
    elif data_type == "bases":
        serializer = ShortBaseSerializer
        search_function = search_bases
    elif data_type == "users":
        serializer = UserSerializerForSearch
        search_function = search_users
    else:
        raise APIException(f"Unknown data type ({data_type})")
    data = serializer(many=True).to_representation(
        search_function(request.user, text=text)
    )
    return Response({"data_type": data_type, "objects": data})
