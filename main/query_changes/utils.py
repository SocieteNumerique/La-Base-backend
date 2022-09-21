from django.db.models import Q


def query_my_related_tags(type_: str):
    return (
        Q(category__relates_to__contains=type_)
        | Q(category__relates_to__isnull=True)
        | Q(category__relates_to="")
    )
