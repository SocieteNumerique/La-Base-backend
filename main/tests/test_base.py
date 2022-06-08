from django.test import TestCase
from django.urls import reverse

from main.factories import UserFactory
from main.tests.test_utils import authenticate


class TestBaseView(TestCase):
    @authenticate
    def test_add_base(self):
        url = reverse("base-list")
        res = self.client.post(url, {"title": "My base"})
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.data["owner"]["id"], authenticate.user.pk)

    @authenticate
    def test_cannot_add_base_as_other_user(self):
        user = UserFactory.create()
        url = reverse("base-list")
        res = self.client.post(url, {"title": "My base", "owner": user.pk})
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.data["owner"]["id"], authenticate.user.pk)

    def test_anonymous_cannot_create_base(self):
        url = reverse("base-list")
        res = self.client.post(url, {"title": "My base"})
        self.assertEqual(res.status_code, 400)
