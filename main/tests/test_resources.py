from django.test import TestCase
from django.urls import reverse

from main.factories import BaseFactory, ResourceFactory, TagFactory
from main.models import ExternalProducer
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

    @authenticate
    def test_can_edit_resource_tags(self):
        base = BaseFactory.create(owner=authenticate.user)
        resource = ResourceFactory.create(root_base=base)
        url = reverse("resource-detail", args=[resource.pk])

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

    @authenticate
    def test_can_edit_resource_creator(self):
        base = BaseFactory.create(owner=authenticate.user)
        resource = ResourceFactory.create(root_base=base)
        url = reverse("resource-detail", args=[resource.pk])

        response = self.client.patch(
            url, {"creator": authenticate.user.pk}, content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["creator"], authenticate.user.pk)

        response = self.client.patch(
            url, {"creator": None}, content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["creator"], None)

    @authenticate
    def test_can_edit_creator_bases(self):
        base1 = BaseFactory.create(owner=authenticate.user)
        base2 = BaseFactory.create(owner=authenticate.user)
        resource = ResourceFactory.create(root_base=base1)
        url = reverse("resource-detail", args=[resource.pk])

        response = self.client.patch(
            url, {"creatorBases": [base1.pk, base2.pk]}, content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["creatorBases"], [base1.pk, base2.pk])

        response = self.client.patch(
            url, {"creatorBases": []}, content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["creatorBases"], [])

    @authenticate
    def test_can_edit_external_producers(self):
        base1 = BaseFactory.create(owner=authenticate.user)
        resource = ResourceFactory.create(root_base=base1)
        url = reverse("resource-detail", args=[resource.pk])

        # adding an external producer
        new_data = {"name": "Name", "emailContact": "bla@mail.com"}
        response = self.client.patch(
            url, {"externalProducers": [new_data]}, content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        res_producers = response.json()["externalProducers"]
        self.assertEqual(len(res_producers), 1)
        producer = res_producers[0]
        self.assertEqual(producer["name"], new_data["name"])
        self.assertEqual(producer["emailContact"], new_data["emailContact"])
        self.assertEqual(producer["resource"], resource.pk)

        # removing the producer
        response = self.client.patch(
            url, {"externalProducers": []}, content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["externalProducers"]), 0)
        self.assertEqual(ExternalProducer.objects.count(), 0)

        # re-adding
        response = self.client.patch(
            url, {"externalProducers": [new_data]}, content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        # adding a new producer and remove the old one at the same time
        new_data2 = {"name": "Name", "emailContact": "other@mail.com"}
        response = self.client.patch(
            url, {"externalProducers": [new_data2]}, content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        res_producers = response.json()["externalProducers"]
        self.assertEqual(len(res_producers), 1)
        producer = res_producers[0]
        self.assertEqual(producer["name"], new_data2["name"])
        self.assertEqual(producer["emailContact"], new_data2["emailContact"])
        self.assertEqual(producer["resource"], resource.pk)
        self.assertEqual(ExternalProducer.objects.count(), 1)

        # can add a producer with a tag
        tag = TagFactory.create()
        new_data = {
            "name": "Name",
            "emailContact": "bla@mail.com",
            "occupation": tag.pk,
        }
        response = self.client.patch(
            url, {"externalProducers": [new_data]}, content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        res_producers = response.json()["externalProducers"]
        self.assertEqual(len(res_producers), 1)
        producer = res_producers[0]
        self.assertEqual(producer["occupation"], tag.pk)

        # can edit a producer's tag and name
        tag2 = TagFactory.create()
        new_data = {
            "name": "Other name",
            "emailContact": "bla@mail.com",
            "occupation": tag2.pk,
        }
        response = self.client.patch(
            url, {"externalProducers": [new_data]}, content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        res_producers = response.json()["externalProducers"]
        self.assertEqual(len(res_producers), 1)
        producer = res_producers[0]
        self.assertEqual(producer["occupation"], tag2.pk)
        self.assertEqual(producer["name"], new_data["name"])
