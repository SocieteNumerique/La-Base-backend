from django.db.models import Q, When, Case, Value
from main.models.user import User

from main.models.models import Base, Resource


def bases_queryset_for_user(user: User, init_queryset=Base.objects, full=True):
    init_queryset = (
        init_queryset.select_related("owner")
        .prefetch_related("tags__category")
        .prefetch_related("tags")
    )
    if user.is_superuser:
        return init_queryset.annotate(
            can_write=Value(True), can_add_resources=Value(True)
        )

    if user.is_anonymous:
        return init_queryset.filter(state="public").annotate(
            can_write=Value(False), can_add_resources=Value(False)
        )

    user_tags = user.tags.all()
    state_query = Q(state="public")
    # TODO use next line when we have subscribe option so that they can see and ask access
    # state_query = Q(state="public") if full else ~Q(state="draft")

    bases_write_access_pks = init_queryset.filter(
        Q(owner=user) | Q(admins=user)
    ).values_list("pk", flat=True)
    bases_can_add_resources_pks = init_queryset.filter(
        Q(owner=user)
        | Q(admins=user)
        | (Q(contributor_tags__in=user_tags) | Q(contributors=user))
    ).values_list("pk", flat=True)
    bases_with_read_access_pks = init_queryset.filter(
        state_query
        | (
            Q(state="private")
            & (Q(authorized_users=user) | Q(authorized_user_tags__in=user_tags))
        )
    ).values_list("pk", flat=True)
    all_bases_pks = list(
        set(bases_write_access_pks)
        .union(set(bases_with_read_access_pks))
        .union(set(bases_can_add_resources_pks))
    )

    return init_queryset.filter(pk__in=all_bases_pks).annotate(
        can_write=Case(
            When(
                Q(pk__in=bases_write_access_pks),
                then=Value(True),
            ),
            default=Value(False),
        ),
        can_add_resources=Case(
            When(
                Q(pk__in=bases_can_add_resources_pks),
                then=Value(True),
            ),
            default=Value(False),
        ),
    )


def resources_queryset_for_user(user: User, init_queryset=Resource.objects, full=True):
    init_queryset = (
        init_queryset.prefetch_related("root_base")
        .prefetch_related("tags")
        .prefetch_related("root_base__contributor_tags")
    )

    if user.is_superuser:
        return init_queryset.annotate(can_write=Value(True))

    if user.is_anonymous:
        return init_queryset.filter(state="public").annotate(can_write=Value(False))

    user_tags = user.tags.all()
    necessary_state_query = Q(state="public")
    # TODO use next line when we have subscribe option so that they can see and ask access
    # necessary_state_query = Q(state="public") if full else ~Q(state="draft")
    resources_with_write_access_pks = init_queryset.filter(
        Q(root_base__owner=user)
        | Q(root_base__admins=user)
        | Q(creator=user)
        | (
            Q(root_base__contributor_tags__in=user_tags)
            | Q(root_base__contributors=user)
        )
    ).values_list("pk", flat=True)
    resources_with_read_access_pks = init_queryset.filter(
        necessary_state_query
        | Q(authorized_users=user)
        | Q(authorized_user_tags__in=user_tags)
        | Q(root_base__authorized_users=user)
        | Q(root_base__authorized_user_tags__in=user_tags)
    ).values_list("pk", flat=True)
    all_pks = list(
        set(resources_with_write_access_pks).union(set(resources_with_read_access_pks))
    )

    return init_queryset.filter(pk__in=all_pks).annotate(
        can_write=Case(
            When(
                Q(pk__in=resources_with_write_access_pks),
                then=Value(True),
            ),
            default=Value(False),
        ),
    )
