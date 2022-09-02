import datetime

from django.test import TestCase
from django.urls import reverse
from freezegun import freeze_time

from main.factories import ResourceFactory, BaseFactory
from main.models import ResourceVisit


class TestVisitCounts(TestCase):
    def test_resource_visits(self):
        resource = ResourceFactory.create()
        self.assertEqual(resource.visit_count, 0)
        url = reverse(
            "increment-visit-count",
            kwargs={"object_type": "resource", "pk": resource.pk},
        )
        self.client.get(url)
        self.assertEqual(resource.visit_count, 1)

        # second view does not create another visit
        self.client.get(url)
        self.assertEqual(resource.visit_count, 1)

        # view from another day creates a visit
        with freeze_time("2012-01-01"):
            self.client.get(url)
        self.assertEqual(resource.visit_count, 2)

        # view from another IP creates a visit
        self.client.get(url)
        self.assertEqual(resource.visit_count, 2)
        visit = ResourceVisit.objects.get(date=datetime.date.today())
        visit.ip_hash = "fake hash"
        visit.save()
        self.client.get(url)
        self.assertEqual(resource.visit_count, 3)

    def test_base_visits(self):
        base = BaseFactory.create()
        self.assertEqual(base.visit_count, 0)
        url = reverse(
            "increment-visit-count",
            kwargs={"object_type": "base", "pk": base.pk},
        )
        self.client.get(url)
        self.assertEqual(base.visit_count, 1)

        # second view does not create another visit
        self.client.get(url)
        self.assertEqual(base.visit_count, 1)
