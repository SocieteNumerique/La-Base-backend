from collections import OrderedDict
from math import ceil

from django.db.models import QuerySet
from rest_framework import pagination

from main.models import Base, User, Collection
from moine_back.settings import RESOURCE_PAGE_SIZE


class Object(object):
    pass


def paginated_resources_from_qs(qs: QuerySet, page: int, context=None):
    if context is None:
        context = {}
    from main.serializers.base_resource_serializers import ShortResourceSerializer

    paginator = pagination.PageNumberPagination()
    paginator.page_size = RESOURCE_PAGE_SIZE
    fake_request = Object()
    fake_request.query_params = {"page": page}
    page = paginator.paginate_queryset(qs, fake_request)
    serializer = ShortResourceSerializer(page, many=True, context=context)
    return OrderedDict(
        [
            ("count", paginator.page.paginator.count),
            (
                "page_count",
                ceil(paginator.page.paginator.count / RESOURCE_PAGE_SIZE),
            ),
            ("results", serializer.data),
        ]
    )


def paginated_resources_from_base(
    base: Base, user: User, page: int, context=None, include_drafts=True
):
    if context is None:
        context = {}
    qs = base.resources_for_user(user, include_drafts=include_drafts).order_by(
        "-created"
    )
    return paginated_resources_from_qs(qs, page, context)


def get_paginated_resources_from_collection(
    collection: Collection, user: User, page=1, context=None
):
    if context is None:
        context = {}
    from main.query_changes.permissions import resources_queryset_for_user
    from main.query_changes.stats_annotations import resources_queryset_with_stats

    qs = resources_queryset_with_stats(
        resources_queryset_for_user(user, collection.resources)
    )

    return paginated_resources_from_qs(qs, page)
