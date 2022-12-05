from django.test import TestCase
from django.urls import reverse

from main.factories import IntroFactory
from main.tests.test_utils import authenticate


class TestVisitCounts(TestCase):
    def test_can_create_intro(self):
        IntroFactory.create()

    def test_intros_are_ordered(self):
        IntroFactory.create(page="page", slug="0", order=1)
        IntroFactory.create(page="page", slug="1", order=3)
        IntroFactory.create(page="page", slug="2", order=0)

        url = reverse("intro-list")
        res = self.client.get(url).json()
        self.assertListEqual([obj["slug"] for obj in res], ["2", "0", "1"])
        # no intro has been seen for anonymous
        self.assertEqual(any(obj["seen"] for obj in res), False)

    @authenticate
    def test_seen_intros(self):
        IntroFactory.create(page="page")
        IntroFactory.create(page="page")
        IntroFactory.create(page="other_page")
        url = reverse("intro-list")
        res = self.client.get(url).json()

        # no intro has been seen
        self.assertEqual(any(obj["seen"] for obj in res), False)

        # mark "page" seen
        mark_url = reverse("mark-intros-seen-for-page", args=["page"])
        res = self.client.get(mark_url)
        self.assertEqual(res.status_code, 201)

        # intros for "page" should now be seen, others not
        res = self.client.get(url).json()
        self.assertEqual(all(obj["seen"] for obj in res if obj["page"] == "page"), True)
        self.assertEqual(
            any(obj["seen"] for obj in res if obj["page"] != "page"), False
        )

        # make sure marking seen another time does not crash
        res = self.client.get(mark_url)
        self.assertEqual(res.status_code, 200)
