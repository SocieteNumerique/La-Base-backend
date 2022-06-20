from django.test import TestCase
from django.urls import reverse

from main.factories import (
    UserFactory,
    BaseFactory,
    ResourceFactory,
    CollectionFactory,
    TagFactory,
    TagCategoryFactory,
)
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

    @authenticate
    def test_add_base_with_contributor_tags(self):
        url = reverse("base-list")
        tag = TagFactory.create()
        res = self.client.post(
            url,
            {"title": "My base", "contributor_tags": [tag.pk]},
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()["contributorTags"], [tag.pk])

    def specific_tag_category_is_sent(self, slug, property_name):
        base = BaseFactory(owner=authenticate.user)
        tc = TagCategoryFactory(slug=slug, relates_to="Base")
        tag = tc.tags.first()
        base.tags.add(tag)

        url = reverse("base-detail", args=[base.pk])
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertListEqual(res.json()[property_name], [tag.id])

        url = reverse("base-list")
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        data_my_base = next(
            base_data for base_data in res.json() if base_data["id"] == base.pk
        )
        self.assertListEqual(data_my_base[property_name], [tag.id])

    @authenticate
    def test_specific_tag_categories_are_sent(self):
        self.specific_tag_category_is_sent(
            "general_00participantType", "participantTypeTags"
        )
        self.specific_tag_category_is_sent("territory_00city", "territoryTags")

    @authenticate
    def test_update_base_admins(self):
        users1 = [UserFactory.create() for _ in range(3)]
        users2 = [UserFactory.create() for _ in range(3)]
        users2.append(users1[0])
        base = BaseFactory.create(owner=authenticate.user)
        base.admins.set(users1)

        url = reverse("base-detail", args=[base.pk])
        res = self.client.patch(
            url,
            {"admins": [{"id": user.pk} for user in users2]},
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200)
        self.assertSetEqual(
            {admin_data["id"] for admin_data in res.json()["admins"]},
            {user.id for user in users2},
        )


class TestPin(TestCase):
    @authenticate
    def test_root_is_pinned(self):
        resource = ResourceFactory(
            creator=authenticate.user,
            is_public=True,
            root_base__owner=authenticate.user,
        )
        url = reverse("resource-detail", args=[resource.pk])
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        base_pin = next(
            base_pin
            for base_pin in res.data["bases_pinned_in"]
            if base_pin["id"] == resource.root_base_id
        )
        self.assertTrue(base_pin["is_pinned"])

        collection = CollectionFactory(base__owner=authenticate.user)
        url = reverse("collection-detail", args=[collection.pk])
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        base_pin = next(
            base_pin
            for base_pin in res.data["bases_pinned_in"]
            if base_pin["id"] == collection.base_id
        )
        self.assertTrue(base_pin["is_pinned"])

    @authenticate
    def test_bases_pinned_in_contains_exactly_my_bases(self):
        base = BaseFactory(owner=authenticate.user)
        other_base = BaseFactory(owner=authenticate.user)

        resource = ResourceFactory(
            creator=authenticate.user, is_public=True, root_base=base
        )
        url = reverse("resource-detail", args=[resource.pk])
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertSetEqual(
            {base_pin["id"] for base_pin in res.data["bases_pinned_in"]},
            {resource.root_base_id, other_base.id},
        )

        collection = CollectionFactory(base=base)
        url = reverse("collection-detail", args=[collection.pk])
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertSetEqual(
            {base_pin["id"] for base_pin in res.data["bases_pinned_in"]},
            {collection.base_id, other_base.id},
        )

    def pin_and_test(self, base, url):
        res = self.client.patch(
            url, {"id": base.id, "is_pinned": True}, content_type="application/json"
        )
        self.assertEqual(res.status_code, 200)
        base_pin = next(base_pin for base_pin in res.data if base_pin["id"] == base.id)
        self.assertTrue(base_pin["is_pinned"])

    @authenticate
    def test_can_pin_not_writable_instance(self):
        # read
        user = UserFactory.create()
        base = BaseFactory(owner=authenticate.user)

        resource = ResourceFactory(creator=user, is_public=True, is_draft=False)
        url = reverse("resource-detail", args=[resource.pk])
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(
            any(base_pin["id"] == base.id for base_pin in res.data["bases_pinned_in"])
        )

        collection = CollectionFactory(base__is_public=True)
        url = reverse("collection-detail", args=[collection.pk])
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(
            any(base_pin["id"] == base.id for base_pin in res.data["bases_pinned_in"])
        )

        # write
        url = reverse("resource-pin", args=[resource.pk])
        self.pin_and_test(base, url)

        url = reverse("collection-pin", args=[collection.pk])
        self.pin_and_test(base, url)
