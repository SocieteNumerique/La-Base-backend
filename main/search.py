from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Q

from main.models import Tag
from main.query_changes.permissions import (
    bases_queryset_for_user,
    resources_queryset_for_user,
)
from main.query_changes.stats_annotations import (
    resources_queryset_with_stats,
    bases_queryset_with_stats,
)

BASES_SEARCH_FIELDS = ["title"]
RESOURCES_SEARCH_FIELDS = ["title", "description"]
USERS_SEARCH_FIELDS = ["first_name", "last_name", "email"]
IS_POSTGRESQL_DB = "postgresql" in settings.DATABASES["default"]["ENGINE"]
SEARCH_KEY_PARAM = "unaccent__icontains" if IS_POSTGRESQL_DB else "icontains"


def filter_queryset(qs, text, search_fields, tag_operator, tags):
    filter_ = Q()
    if text:
        for field in search_fields:
            filter_ = filter_ | Q(**{f"{field}__{SEARCH_KEY_PARAM}": text})
    qs = qs.filter(filter_)
    if tags:
        if tag_operator == "OR":
            qs = qs.filter(tags__in=tags)
        else:
            for tag in tags:
                qs = qs.filter(tags=tag)
    return qs


def search_bases(user, text, tag_operator="OR", tags=None):
    if tags is None:
        tags = []
    qs = bases_queryset_with_stats(bases_queryset_for_user(user, full=False))
    qs = filter_queryset(qs, text, BASES_SEARCH_FIELDS, tag_operator, tags)
    qs = qs.order_by("-modified")
    possible_tags = (
        Tag.objects.filter(bases__in=qs).values_list("pk", flat=True).distinct()
    )
    return {"queryset": qs, "possible_tags": possible_tags}


def search_resources(
    user, text, tag_operator="OR", tags=None, restrict_to_base_id=None, live=None
):
    if tags is None:
        tags = []
    qs = resources_queryset_with_stats(
        resources_queryset_for_user(user, restrict_to_base_id=restrict_to_base_id)
    )
    qs = filter_queryset(qs, text, RESOURCES_SEARCH_FIELDS, tag_operator, tags)
    if live is not None:
        if live:
            qs = qs.filter(~Q(state="draft"))
        else:
            qs = qs.filter(Q(state="draft"))
    qs = qs.order_by("-modified")
    possible_tags = (
        Tag.objects.filter(resources__in=qs).values_list("pk", flat=True).distinct()
    )
    return {"queryset": qs, "possible_tags": possible_tags}


def search_users(user, text, tag_operator="OR", tags=None):
    if tags is None:
        tags = []
    User = get_user_model()
    qs = User.objects.all()
    qs = filter_queryset(qs, text, USERS_SEARCH_FIELDS, tag_operator, tags)
    possible_tags = (
        Tag.objects.filter(users__in=qs).values_list("pk", flat=True).distinct()
    )
    return {"queryset": qs, "possible_tags": possible_tags}
