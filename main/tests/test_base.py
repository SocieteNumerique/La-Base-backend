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
from main.serializers.utils import reset_specific_categories
from main.tests.test_utils import authenticate, snake_to_camel_case


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

    @authenticate
    def test_add_base_with_html_script_tag_in_description(self):
        url = reverse("base-list")
        res = self.client.post(
            url,
            {"title": "My base", "description": "<script>test</script>"},
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()["description"], "&lt;script&gt;test&lt;/script&gt;")

    def specific_tag_category_is_sent(self, slug, property_name):
        base = BaseFactory(owner=authenticate.user)
        tc = TagCategoryFactory(slug=slug, relates_to="Base")
        reset_specific_categories()
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
            "externalProducer_00occupation", "participantTypeTags"
        )
        self.specific_tag_category_is_sent("territory_00city", "territoryTags")

    def update_user_list(self, property_name):
        users1 = [UserFactory.create() for _ in range(3)]
        users2 = [UserFactory.create() for _ in range(3)]
        users2.append(users1[0])
        base = BaseFactory.create(owner=authenticate.user)
        property_in_instance = getattr(base, property_name)
        property_in_instance.set(users1)

        caml_case_property_name = snake_to_camel_case(property_name)

        url = reverse("base-detail", args=[base.pk])
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
        self.update_user_list("admins")

    @authenticate
    def test_update_base_authorized_users(self):
        self.update_user_list("authorized_users")

    @authenticate
    def test_update_base_contributors(self):
        self.update_user_list("contributors")


class TestPin(TestCase):
    @authenticate
    def test_root_is_not_pinned(self):
        resource = ResourceFactory(
            creator=authenticate.user,
            state="public",
            root_base__owner=authenticate.user,
        )
        url = reverse("resource-detail", args=[resource.pk])
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["pinned_in_bases"], [])

        collection = CollectionFactory(base__owner=authenticate.user)
        url = reverse("collection-detail", args=[collection.pk])
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["pinned_in_bases"], [])

    @authenticate
    def test_pinned_in_bases_is_empty_by_default(self):
        base = BaseFactory(owner=authenticate.user)
        BaseFactory(owner=authenticate.user)

        resource = ResourceFactory(
            creator=authenticate.user, state="public", root_base=base
        )
        url = reverse("resource-detail", args=[resource.pk])
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertSetEqual(
            set(res.data["pinned_in_bases"]),
            set(),
        )

        collection = CollectionFactory(base=base)
        url = reverse("collection-detail", args=[collection.pk])
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertSetEqual(
            {base_pin["id"] for base_pin in res.data["pinned_in_bases"]},
            set(),
        )

    def pin_and_test(self, base, url):
        res = self.client.patch(
            url, {"id": base.id, "is_pinned": True}, content_type="application/json"
        )
        self.assertEqual(res.status_code, 200)
        self.assertIn(base.id, res.json())

    @authenticate
    def test_can_pin_not_writable_instance(self):
        # read
        user = UserFactory.create()
        base = BaseFactory(owner=authenticate.user)

        resource = ResourceFactory(creator=user, state="public")
        url = reverse("resource-detail", args=[resource.pk])
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)

        collection = CollectionFactory(base__state="public")
        url = reverse("collection-detail", args=[collection.pk])
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)

        # write
        url = reverse("resource-pin", args=[resource.pk])
        self.pin_and_test(base, url)

        url = reverse("collection-pin", args=[collection.pk])
        self.pin_and_test(base, url)

    @authenticate
    def test_contributors_can_pin(self):
        # read
        base = BaseFactory()
        tag = TagFactory(category__relates_to="User")
        base.contributor_tags.add(tag)
        authenticate.user.tags.add(tag)

        resource = ResourceFactory(state="public")
        url = reverse("resource-detail", args=[resource.pk])
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)

        # write
        url = reverse("resource-pin", args=[resource.pk])
        self.pin_and_test(base, url)

    @authenticate
    def test_multiple_pins(self):
        # read
        base = BaseFactory(owner=authenticate.user)

        resource = ResourceFactory(state="public")

        # pin resource
        url = reverse("resource-pin", args=[resource.pk])
        res = self.client.patch(
            url, {"id": base.id, "is_pinned": True}, content_type="application/json"
        )
        self.assertEqual(res.status_code, 200)
        self.assertListEqual(res.json(), [base.id])

        # pin in other base
        base2 = BaseFactory(owner=authenticate.user)
        res = self.client.patch(
            url, {"id": base2.id, "is_pinned": True}, content_type="application/json"
        )
        self.assertEqual(res.status_code, 200)
        self.assertSetEqual(set(res.json()), {base.id, base2.id})

        # remove first pin
        res = self.client.patch(
            url, {"id": base.id, "is_pinned": False}, content_type="application/json"
        )
        self.assertEqual(res.status_code, 200)
        self.assertSetEqual(set(res.json()), {base2.id})

        # remove other pin
        res = self.client.patch(
            url, {"id": base2.id, "is_pinned": False}, content_type="application/json"
        )
        self.assertEqual(res.status_code, 200)
        self.assertSetEqual(set(res.json()), set())
