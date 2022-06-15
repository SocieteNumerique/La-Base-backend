from django.db.models import Q, When, Case, Value
from main.models.user import User

from main.models.models import Base, Resource


def bases_queryset_for_user(user: User, init_queryset=Base.objects):
    if user.is_superuser:
        return init_queryset.annotate(can_write=Value(True))

    if user.is_anonymous:
        return init_queryset.filter(is_public=True).annotate(can_write=Value(False))

    qs = init_queryset.filter(Q(is_public=True) | Q(owner=user) | Q(admins=user))
    return qs.annotate(
        can_write=Case(
            When(Q(owner=user) | Q(admins=user), then=Value(True)), default=Value(False)
        )
    )


def resources_queryset_for_user(user: User, init_queryset=Resource.objects):
    init_queryset = init_queryset.prefetch_related("root_base").prefetch_related("tags")

    if user.is_superuser:
        return init_queryset.annotate(can_write=Value(True))

    if user.is_anonymous:
        return init_queryset.filter(is_public=True, is_draft=False).annotate(
            can_write=Value(False)
        )

    qs = init_queryset.filter(
        Q(is_public=True, is_draft=False)
        | Q(root_base__owner=user)
        | Q(root_base__admins=user)
        | Q(creator=user)
        | Q(groups__users=user)
    )
    return qs.annotate(
        can_write=Case(
            When(
                Q(root_base__owner=user)
                | Q(root_base__admins=user)
                | Q(creator=user)
                | (
                    Q(resource_user_groups__group__users=user)
                    & Q(resource_user_groups__can_write=True)
                ),
                then=Value(True),
            ),
            default=Value(False),
        )
    )
