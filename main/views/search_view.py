from rest_framework import viewsets, mixins
from rest_framework.exceptions import APIException, ParseError
from rest_framework.pagination import PageNumberPagination

from main.models.models import Resource
from main.search import search_resources, search_bases, search_users
from main.serializers.base_resource_serializers import (
    ShortResourceSerializer,
    ShortBaseSerializer,
)
from main.serializers.user_serializer import UserSerializerForSearch


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = "page_size"
    max_page_size = 100


class SearchView(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Resource.objects.all()
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        """Get search results for selected data type."""
        text = self.request.data.get("text", "")
        tag_operator = self.request.data.get("tag_operator", "OR")
        tags = self.request.data.get("tags")
        try:
            data_type = self.request.data["data_type"]
        except KeyError:
            raise ParseError("'data_type' needs to be in request body")
        if data_type == "resources":
            search_function = search_resources
        elif data_type == "bases":
            search_function = search_bases
        elif data_type == "users":
            search_function = search_users
        else:
            raise APIException(f"Unknown data type ({data_type})")
        return search_function(
            self.request.user, text=text, tag_operator=tag_operator, tags=tags
        )

    def get_serializer_class(self):
        data_type = self.request.data["data_type"]
        if data_type == "resources":
            return ShortResourceSerializer
        elif data_type == "bases":
            return ShortBaseSerializer
        elif data_type == "users":
            return UserSerializerForSearch

    def create(self, request, *args, **kwargs):
        """We use create as the request is a POST."""
        search_results = self.get_queryset()
        queryset, possible_tags = (
            search_results["queryset"],
            search_results["possible_tags"],
        )

        queryset = self.filter_queryset(queryset)

        page = self.paginate_queryset(queryset)

        if page is None:
            raise APIException("Missing pagination")

        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(
            {
                "data_type": self.request.data["data_type"],
                "objects": serializer.data,
                "possible_tags": list(possible_tags),
                "text": self.request.data.get("text", ""),
            }
        )
