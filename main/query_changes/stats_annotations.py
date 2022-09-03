from django.db.models import Q, Count, Prefetch

from main.models.models import Resource, Tag


def resources_queryset_with_stats(init_queryset=Resource.objects):
    return (
        init_queryset.annotate(
            nb_files=Count(
                "contents", distinct=True, filter=Q(contents__filecontent__isnull=False)
            ),
        )
        .annotate(
            nb_links=Count(
                "contents", distinct=True, filter=Q(contents__linkcontent__isnull=False)
            ),
        )
        .annotate(visit_count=Count("visits", distinct=True))
    )


def bases_queryset_with_stats(init_queryset=Resource.objects):
    prefetch_supports = Prefetch(
        "tags",
        queryset=Tag.objects.filter(category__slug="indexation_01RessType"),
        to_attr="supports",
    )
    return (
        init_queryset.annotate(
            nb_files=Count(
                "contents", distinct=True, filter=Q(contents__filecontent__isnull=False)
            ),
        )
        .annotate(
            nb_links=Count(
                "contents", distinct=True, filter=Q(contents__linkcontent__isnull=False)
            ),
        )
        .prefetch_related(prefetch_supports)
        .annotate(visit_count=Count("visits", distinct=True))
    )
