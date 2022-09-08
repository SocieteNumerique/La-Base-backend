from django.test import TestCase
from django.urls import reverse

from main.factories import (
    BaseFactory,
    ResourceFactory,
    TagFactory,
    TagCategoryFactory,
    UserFactory,
)
from main.models import Resource
from main.models.models import ExternalProducer
from main.serializers.utils import reset_specific_categories
from main.tests.test_utils import authenticate, snake_to_camel_case


class TestResourceView(TestCase):
    @authenticate
    def test_can_create_resource(self):
        base = BaseFactory.create(owner=authenticate.user)
        url = reverse("resource-list")
        response = self.client.post(url, {"root_base": base.pk, "title": "My title"})
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.json()["canWrite"])
        resource = Resource.objects.get(pk=response.json()["id"])
        self.assertEqual(resource.creator, authenticate.user)

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
        external_producer_tag_category = TagCategoryFactory.create(
            slug="externalProducer_00occupation", relates_to=None
        )
        reset_specific_categories()
        tag = TagFactory.create(category=external_producer_tag_category)
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
        tag2 = TagFactory.create(category=external_producer_tag_category)
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

    def update_user_list(self, property_name):
        users1 = [UserFactory.create() for _ in range(3)]
        users2 = [UserFactory.create() for _ in range(3)]
        users2.append(users1[0])
        resource = ResourceFactory.create(root_base__owner=authenticate.user)
        property_in_instance = getattr(resource, property_name)
        property_in_instance.set(users1)

        caml_case_property_name = snake_to_camel_case(property_name)

        url = reverse("base-detail", args=[resource.pk])
        res = self.client.patch(
            url,
            {caml_case_property_name: [{"id": user.pk} for user in users2]},
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200)

        self.assertSetEqual(
            {user_data["id"] for user_data in res.json()[caml_case_property_name]},
            {user.id for user in users2},
        )

    @authenticate
    def test_update_base_admins(self):
        self.update_user_list("authorized_users")
