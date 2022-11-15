from django.db.models import Q, Count, Prefetch

from main.models.models import Resource, Tag
from main.serializers.utils import SPECIFIC_CATEGORY_SLUGS


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
        .annotate(pinned_count=Count("pinned_in_bases", distinct=True))
    )


def bases_queryset_with_stats(init_queryset=Resource.objects):
    prefetch_tags = Prefetch(
        "tags",
        queryset=Tag.objects.filter(
            category__slug=SPECIFIC_CATEGORY_SLUGS["participant"]
        ),
        to_attr="participant_types",
    )
    return init_queryset.prefetch_related(prefetch_tags).annotate(
        visit_count=Count("visits", distinct=True),
        own_resource_count=Count("resources", distinct=True),
        pinned_resource_count=Count("pinned_resources", distinct=True),
    )
