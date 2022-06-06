from django.conf import settings
from django.db.models import Q
from telescoop_auth.models import User

from main.query_changes.permissions import (
    bases_queryset_for_user,
    resources_queryset_for_user,
)

BASES_SEARCH_FIELDS = ["title"]
RESOURCES_SEARCH_FIELDS = ["title", "description"]
USERS_SEARCH_FIELDS = ["first_name", "last_name"]
IS_POSTGRESQL_DB = "postgresql" in settings.DATABASES["default"]["ENGINE"]
SEARCH_KEY_PARAM = "search" if IS_POSTGRESQL_DB else "contains"


def search_bases(user, text):
    qs = bases_queryset_for_user(user)
    filter_ = Q()
    for field in BASES_SEARCH_FIELDS:
        filter_ = filter_ | Q(**{f"{field}__{SEARCH_KEY_PARAM}": text})
    return qs.filter(filter_)


def search_resources(user, text):
    qs = resources_queryset_for_user(user)
    filter_ = Q()
    for field in RESOURCES_SEARCH_FIELDS:
        filter_ = filter_ | Q(**{f"{field}__{SEARCH_KEY_PARAM}": text})
    return qs.filter(filter_)


def search_users(_, text):
    qs = User.objects
    filter_ = Q()
    for field in USERS_SEARCH_FIELDS:
        filter_ = filter_ | Q(**{f"{field}__{SEARCH_KEY_PARAM}": text})
    return qs.filter(filter_)[:10]
