from django.test import TestCase
from django.urls import reverse

from main.factories import BaseFactory, ResourceFactory
from main.models import Collection
from main.tests.test_utils import authenticate


class TestResourceView(TestCase):
    @authenticate
    def test_can_add_collection(self):
        base = BaseFactory.create(owner=authenticate.user)
        url = reverse("collection-list")
        res = self.client.post(url, {"base": base.pk, "name": "My name"})
        self.assertEqual(res.status_code, 201)

    @authenticate
    def test_can_only_add_resources_linked_to_base(self):
        base = BaseFactory.create(owner=authenticate.user)
        collection = Collection.objects.create(base=base, name="collection")
        url = reverse("collection-detail", args=[collection.pk])
        r1 = ResourceFactory.create(root_base=base)
        res = self.client.patch(
            url, {"resources": [r1.pk]}, content_type="application/json"
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(collection.resources.count(), 1)

        r2 = ResourceFactory.create()
        res = self.client.patch(
            url, {"resources": [r2.pk]}, content_type="application/json"
        )
        self.assertEqual(res.status_code, 400)

    @authenticate
    def test_change_base_ownership_removes_resource_from_collections(self):
        base = BaseFactory.create(owner=authenticate.user)
        collection = Collection.objects.create(base=base, name="collection")
        resource = ResourceFactory.create(root_base=base)
        collection.resources.add(resource)
        url = reverse("collection-detail", args=[collection.pk])
        res = self.client.get(url)
        self.assertListEqual(res.data["resources"], [resource.pk])

        base2 = BaseFactory.create(owner=authenticate.user)
        resource.root_base = base2
        resource.save()
        res = self.client.get(url)
        self.assertListEqual(res.data["resources"], [])

    @authenticate
    def test_update_resources_list(self):
        base = BaseFactory.create(owner=authenticate.user)
        collection = Collection.objects.create(base=base, name="collection")
        resources = [ResourceFactory.create(root_base=base) for _ in range(5)]
        for resource in resources[:3]:
            collection.resources.add(resource)

        url = reverse("collection-detail", args=[collection.pk])
        res = self.client.get(url)
        self.assertListEqual(
            res.data["resources"], [resource.pk for resource in resources[:3]]
        )

        new_pks = [resource.pk for resource in resources[3:]]
        res = self.client.patch(
            url, dict(resources=new_pks), content_type="application/json"
        )
        self.assertListEqual(res.data["resources"], new_pks)

    @authenticate
    def test_base_serializer_includes_collection_data(self):
        base = BaseFactory.create(owner=authenticate.user)
        collection = Collection.objects.create(base=base, name="collection")
        resource = ResourceFactory.create(root_base=base)
        collection.resources.add(resource)
        url = reverse("base-detail", args=[base.pk])
        res = self.client.get(url)
        self.assertEqual(res.data["collections"][0]["resources"], [resource.pk])
