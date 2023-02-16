from django.db.models import (
    Q,
    Count,
    Prefetch,
    FloatField,
    Subquery,
    OuterRef,
    Func,
    F,
    Case,
    When,
)
from django.db.models.functions import Coalesce

from main.models import Evaluation
from main.models.evaluations import get_all_criteria
from main.models.models import Resource, Tag, Base
from main.serializers.utils import SPECIFIC_CATEGORY_SLUGS


def resources_queryset_with_stats(init_queryset=Resource.objects):
    qs = (
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
        .prefetch_related("evaluations")
    )

    for criterion in get_all_criteria():
        qs = qs.annotate(
            **{
                f"{criterion.slug}_count": Count(
                    "evaluations",
                    distinct=True,
                    filter=Q(evaluations__criterion__slug=criterion.slug),
                )
            }
        )

        mean_subquery = (
            Evaluation.objects.filter(
                resource=OuterRef("id"), criterion__slug=criterion.slug
            )
            .annotate(
                total=Coalesce(
                    Func("evaluation", function="Sum", output_field=FloatField()), 0.0
                ),
                count=Func("evaluation", function="Count", output_field=FloatField()),
            )
            .values("total", "count")
            .annotate(
                mean=Case(
                    When(count=0, then=None),
                    default=(1.0 * F("total")) / (1.0 * F("count")),
                )
            )
            .values("mean")
        )

        qs = qs.annotate(
            **{
                f"{criterion.slug}_mean": Subquery(mean_subquery),
            }
        )

    return qs


def bases_queryset_with_stats(init_queryset=Base.objects):
    prefetch_tags = Prefetch(
        "tags",
        queryset=Tag.objects.filter(
            category__slug=SPECIFIC_CATEGORY_SLUGS["participant"]
        ),
        to_attr="participant_types",
    )
    return init_queryset.prefetch_related(prefetch_tags).prefetch_related("bookmarks")
