from django.test import TestCase
from django.urls import reverse

from main.factories import BaseFactory, ResourceFactory, TagFactory
from main.tests.test_utils import authenticate


class TestResourceView(TestCase):
    @authenticate
    def test_can_update_resource(self):
        base = BaseFactory.create(owner=authenticate.user)
        resource = ResourceFactory.create(root_base=base)
        url = reverse("resource-detail", args=[resource.pk])
        response = self.client.patch(
            url, {"title": "updated title"}, content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["title"], "updated title")

        # we can add a tag
        tag = TagFactory.create()
        response = self.client.patch(
            url, {"tags": [tag.pk]}, content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["tags"], [tag.pk])

        # we can change linked tags
        new_tag = TagFactory.create()
        response = self.client.patch(
            url, {"tags": [new_tag.pk]}, content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["tags"], [new_tag.pk])
