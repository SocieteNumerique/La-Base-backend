from django.test import TestCase
from django.urls import reverse

from main.factories import UserFactory, BaseFactory
from main.tests.test_utils import authenticate


class TestBaseBookmark(TestCase):
    @authenticate
    def test_base_bookmark(self):
        base = BaseFactory.create(owner=authenticate.user)

        # can create BaseBookmark
        res = self.client.get(reverse("base-detail", args=[base.pk]))
        self.assertEqual(res.status_code, 200)
        self.assertFalse(res.json()["bookmarked"])
        res = self.client.get(
            reverse("base-bookmark", args=[base.pk]),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 201)
        res = self.client.get(reverse("base-detail", args=[base.pk]))
        self.assertTrue(res.json()["bookmarked"])

        # not accessible by another user
        other_user = UserFactory.create()
        self.client.force_login(user=other_user)
        base.admins.add(other_user)
        res = self.client.get(reverse("base-detail", args=[base.pk]))
        self.assertFalse(res.json()["bookmarked"])

        #  can destroy BaseBookmark
        self.client.force_login(user=authenticate.user)
        res = self.client.get(
            reverse("base-remove-bookmark", args=[base.pk]),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 204)
        res = self.client.get(reverse("base-detail", args=[base.pk]))
        self.assertFalse(res.json()["bookmarked"])
