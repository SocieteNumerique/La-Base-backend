from django.test import TestCase
from django.urls import reverse

from main.factories import (
    EvaluationFactory,
    ResourceFactory,
    BaseFactory,
    CriterionFactory,
)
from main.models.evaluations import get_all_criteria
from main.tests.test_utils import authenticate


class TestEvaluations(TestCase):
    url = reverse("evaluation-list")

    @authenticate
    def test_can_evaluate(self):
        base = BaseFactory.create(owner=authenticate.user)
        resource = ResourceFactory.create(root_base=base)
        criterion = CriterionFactory.create()
        res = self.client.post(
            self.url,
            {
                "resource": resource.pk,
                "evaluation": 1,
                "comment": "My comment",
                "criterion": criterion.slug,
            },
        )
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.data["evaluation"], 1)
        self.assertEqual(res.data["comment"], "My comment")

        # can change evaluation
        res = self.client.post(
            self.url,
            {
                "resource": resource.pk,
                "evaluation": 2,
                "comment": "changed",
                "criterion": criterion.slug,
            },
        )
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.data["evaluation"], 2)
        self.assertEqual(res.data["comment"], "changed")

    @authenticate
    def test_cannot_evaluate_when_no_read_access(self):
        resource = ResourceFactory.create()
        criterion = CriterionFactory.create()
        res = self.client.post(
            self.url,
            {
                "resource": resource.pk,
                "evaluation": True,
                "comment": "my comment",
                "criterion": criterion.slug,
            },
        )
        self.assertEqual(res.status_code, 400)

    def get_resource_stats(self, resource):
        url = reverse("resource-detail", args=[resource.pk])
        return self.client.get(url).data["stats"]

    @authenticate
    def test_can_remove_evaluation(self):
        resource = ResourceFactory.create(state="public")
        evaluation = EvaluationFactory.create(resource=resource, user=authenticate.user)
        self.assertEqual(resource.evaluations.count(), 1)
        url = reverse(
            "evaluation-detail", args=[f"{resource.pk}-{evaluation.criterion.slug}"]
        )
        res = self.client.delete(url)
        self.assertEqual(res.status_code, 204)
        self.assertEqual(resource.evaluations.count(), 0)

    @authenticate
    def test_resource_evaluation_stats(self):
        criterion = CriterionFactory.create()
        # refresh cache
        if hasattr(get_all_criteria, "criteria"):
            get_all_criteria.__delattr__("criteria")

        # testing on two resources to make sure evaluations on one resource
        # doesn't mess up other resources
        for i in range(2):
            resource = ResourceFactory.create(state="public")
            EvaluationFactory.create(
                resource=resource, evaluation=4, criterion=criterion
            )
            stats = self.get_resource_stats(resource)
            self.assertEqual(stats[f"{criterion.slug}_count"], 1)
            self.assertEqual(stats[f"{criterion.slug}_mean"], 4)
            EvaluationFactory.create(
                resource=resource, evaluation=2, criterion=criterion
            )
            stats = self.get_resource_stats(resource)
            self.assertEqual(stats[f"{criterion.slug}_count"], 2)
            self.assertEqual(stats[f"{criterion.slug}_mean"], 3)
            EvaluationFactory.create(
                resource=resource, evaluation=0, criterion=criterion
            )
            stats = self.get_resource_stats(resource)
            self.assertEqual(stats[f"{criterion.slug}_count"], 3)
            self.assertEqual(stats[f"{criterion.slug}_mean"], 2)
            # giving twice same grades, there have been issues when
            # multiple grades are equal
            EvaluationFactory.create(
                resource=resource, evaluation=4, criterion=criterion
            )
            stats = self.get_resource_stats(resource)
            self.assertEqual(stats[f"{criterion.slug}_count"], 4)
            self.assertEqual(stats[f"{criterion.slug}_mean"], 2.5)
