import datetime

from django.db import models

from main.models.user import User
from main.models.models import Resource
from main.models.utils import TimeStampedModel

EVALUATIONS = [
    (0, "pas abouti"),
    (1, "peu abouti"),
    (2, "moyennement abouti"),
    (3, "abouti"),
    (4, "très abouti"),
]
MIN_EVALUATION = min(evaluation[0] for evaluation in EVALUATIONS)
MAX_EVALUATION = max(evaluation[0] for evaluation in EVALUATIONS)


class Criterion(models.Model):
    class Meta:
        verbose_name = "critère d'évaluation"

    name = models.CharField(max_length=50, verbose_name="nom")
    description = models.CharField(max_length=200, verbose_name="description")
    order = models.IntegerField(verbose_name="ordre du critère")
    slug = models.CharField(
        max_length=30,
        verbose_name="nom technique (ne pas changer)",
        unique=True,
        primary_key=True,
    )

    def __str__(self):
        return self.name


class Evaluation(TimeStampedModel):
    class Meta:
        unique_together = ("resource", "user", "criterion")

    resource = models.ForeignKey(
        Resource, on_delete=models.CASCADE, related_name="evaluations"
    )
    criterion = models.ForeignKey(Criterion, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    evaluation = models.PositiveSmallIntegerField(choices=EVALUATIONS)
    comment = models.TextField()


def get_all_criteria():
    """
    Fetch criteria with 1 minute cache to avoid criteria being
    fetched mutliple times per request.
    """
    now = datetime.datetime.now()
    if hasattr(get_all_criteria, "criteria") and (
        (now - getattr(get_all_criteria, "last_fetched", now)).total_seconds() < 60
    ):
        return get_all_criteria.criteria

    get_all_criteria.criteria = Criterion.objects.all()
    get_all_criteria.last_fetched = now

    return get_all_criteria.criteria
