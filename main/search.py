from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Q

from main.models import Tag
from main.query_changes.permissions import (
    bases_queryset_for_user,
    resources_queryset_for_user,
)

BASES_SEARCH_FIELDS = ["title"]
RESOURCES_SEARCH_FIELDS = ["title", "description"]
USERS_SEARCH_FIELDS = ["first_name", "last_name"]
IS_POSTGRESQL_DB = "postgresql" in settings.DATABASES["default"]["ENGINE"]
SEARCH_KEY_PARAM = "search" if IS_POSTGRESQL_DB else "contains"


def filter_queryset(qs, text, search_fields, tag_operator, tags):
    filter_ = Q()
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
    qs = bases_queryset_for_user(user)
    qs = filter_queryset(qs, text, BASES_SEARCH_FIELDS, tag_operator, tags)
    possible_tags = (
        Tag.objects.filter(bases__in=qs).values_list("pk", flat=True).distinct()
    )
    return {"queryset": qs, "possible_tags": possible_tags}


def search_resources(user, text, tag_operator="OR", tags=None):
    if tags is None:
        tags = []
    qs = resources_queryset_for_user(user)
    qs = filter_queryset(qs, text, RESOURCES_SEARCH_FIELDS, tag_operator, tags)
    possible_tags = (
        Tag.objects.filter(ressources__in=qs).values_list("pk", flat=True).distinct()
    )
    return {"queryset": qs, "possible_tags": possible_tags}


def search_users(user, text, tag_operator="OR", tags=None):
    if tags is None:
        tags = []
    User = get_user_model()
    qs = User.objects.all()
    qs = filter_queryset(qs, text, USERS_SEARCH_FIELDS, tag_operator, tags)
    possible_tags = (
        Tag.objects.filter(ressources__in=qs).values_list("pk", flat=True).distinct()
    )
    return {"queryset": qs, "possible_tags": possible_tags}