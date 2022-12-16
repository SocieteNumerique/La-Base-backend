from django.db.models import Q, Count, Prefetch

from main.models.models import Resource, Tag, Base
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
        .prefetch_related(
            Prefetch(
                "pinned_in_bases",
                queryset=Base.objects.filter(state="public"),
                to_attr="pinned_in_public_bases",
            )
        )
        .annotate(pin_count=Count("pinned_in_bases", distinct=True))
        .annotate(
            public_pin_count=Count(
                "pinned_in_bases",
                distinct=True,
                filter=Q(pinned_in_bases__state="public"),
            ),
        )
    )


def bases_queryset_with_stats(init_queryset=Base.objects):
    prefetch_tags = Prefetch(
        "tags",
        queryset=Tag.objects.filter(
            category__slug=SPECIFIC_CATEGORY_SLUGS["participant"]
        ),
        to_attr="participant_types",
    )
    return init_queryset.prefetch_related(prefetch_tags).prefetch_related("bookmarks")
