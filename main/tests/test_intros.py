from django.test import TestCase
from django.urls import reverse

from main.factories import IntroFactory
from main.tests.test_utils import authenticate


class TestVisitCounts(TestCase):
    def test_can_create_intro(self):
        IntroFactory.create()

    def test_intros_are_ordered(self):
        IntroFactory.create(slug="slug", title="0", order=1)
        IntroFactory.create(slug="slug", title="1", order=3)
        IntroFactory.create(slug="slug", title="2", order=0)

        url = reverse("intro-list")
        res = self.client.get(url).json()
        self.assertListEqual([obj["title"] for obj in res], ["2", "0", "1"])
        # no intro has been seen for anonymous
        self.assertEqual(any(obj["seen"] for obj in res), False)

    @authenticate
    def test_seen_intros(self):
        IntroFactory.create(slug="slug")
        IntroFactory.create(slug="slug")
        IntroFactory.create(slug="slug2")
        IntroFactory.create(slug="other_slug")
        url = reverse("intro-list")
        res = self.client.get(url).json()

        # no intro has been seen
        self.assertEqual(any(obj["seen"] for obj in res), False)

        # mark "slug" seen
        mark_url = reverse("mark-intros-seen-for-slugs", args=["slug,slug2"])
        res = self.client.get(mark_url)
        self.assertEqual(res.status_code, 200)

        # intros for "slug" and "slug2" should now be seen, others not
        res = self.client.get(url).json()
        self.assertEqual(
            all(obj["seen"] for obj in res if obj["slug"] in ["slug", "slug2"]), True
        )
        self.assertEqual(
            any(obj["seen"] for obj in res if obj["slug"] == "other_slug"), False
        )

        # make sure marking seen another time does not crash
        res = self.client.get(mark_url)
        self.assertEqual(res.status_code, 200)
