from django.test import TestCase
from django.urls import reverse

from main.factories import (
    BaseFactory,
    ResourceFactory,
    CollectionFactory,
    BaseSectionFactory,
)
from main.models.models import BASE_SECTION_TYPE
from main.tests.test_utils import authenticate


class TestResourceView(TestCase):
    @authenticate
    def test_can_add_section_with_resources(self):
        base = BaseFactory.create(owner=authenticate.user)
        resource = ResourceFactory.create(root_base=base)
        url = reverse("base-section-list")
        res = self.client.post(
            url,
            {
                "base": base.pk,
                "title": "My name",
                "description": "My description",
                "type": BASE_SECTION_TYPE[0][0],
                "resources": [resource.pk],
            },
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 201)
        self.assertListEqual(res.json()["resources"], [resource.pk])

    @authenticate
    def test_can_add_section_with_collections(self):
        base = BaseFactory.create(owner=authenticate.user)
        collection = CollectionFactory.create(base=base)
        url = reverse("base-section-list")
        res = self.client.post(
            url,
            {
                "base": base.pk,
                "title": "My name",
                "description": "My description",
                "type": BASE_SECTION_TYPE[0][0],
                "collections": [collection.pk],
            },
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 201)
        self.assertListEqual(res.json()["collections"], [collection.pk])

    @authenticate
    def test_can_update_section(self):
        base = BaseFactory.create(owner=authenticate.user)
        old_resource = ResourceFactory.create(root_base=base)
        new_resource = ResourceFactory.create(root_base=base)
        base_section = BaseSectionFactory.create(base=base, resources=[old_resource.pk])

        url = reverse("base-section-detail", args=[base_section.pk])
        res = self.client.patch(
            url,
            {
                "base": base.pk,
                "title": "My new name",
                "description": "My new description",
                "type": BASE_SECTION_TYPE[0][0],
                "resources": [new_resource.pk],
            },
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200)
        self.assertListEqual(res.json()["resources"], [new_resource.pk])

    @authenticate
    def test_can_delete_section(self):
        base = BaseFactory.create(owner=authenticate.user)
        resource = ResourceFactory.create(root_base=base)
        base_section = BaseSectionFactory.create(base=base, resources=[resource.pk])

        url = reverse("base-section-detail", args=[base_section.pk])
        res = self.client.delete(url)
        self.assertEqual(res.status_code, 204)

    @authenticate
    def test_can_sort_sections(self):
        base = BaseFactory.create(owner=authenticate.user)
        resource = ResourceFactory.create(root_base=base)
        base_section_1 = BaseSectionFactory.create(
            base=base, resources=[resource.pk], position=0
        )
        base_section_2 = BaseSectionFactory.create(
            base=base, resources=[resource.pk], position=1
        )

        url = reverse("base-section-sort")
        res = self.client.patch(
            url,
            {
                "base": base.pk,
                "sections": [base_section_2.pk, base_section_1.pk],
            },
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200)
        self.assertListEqual(res.json(), [base_section_2.pk, base_section_1.pk])
        base_section_1.refresh_from_db()
        base_section_2.refresh_from_db()
        self.assertEqual(base_section_2.position, 0)
        self.assertEqual(base_section_1.position, 1)
