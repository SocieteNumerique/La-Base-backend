from django.contrib.auth.models import AnonymousUser
from django.test import TestCase
from django.urls import reverse

from main.factories import ResourceFactory, BaseFactory, TagFactory
from main.models import Resource
from main.search import search_resources, search_bases
from main.tests.test_utils import authenticate
from main.views.search_view import SearchView, StandardResultsSetPagination


class TestSearch(TestCase):
    def test_anonymous_search_on_resources_public_data(self):
        ResourceFactory.create(title="MyTitle", state="public")
        self.assertEqual(
            search_resources(AnonymousUser(), "MyTitle")["queryset"].count(), 1
        )
        self.assertEqual(
            search_resources(AnonymousUser(), "OtherTitle")["queryset"].count(), 0
        )

    def test_anonymous_search_on_resources_private_data(self):
        ResourceFactory.create(title="MyTitle", state="private")
        self.assertEqual(
            search_resources(AnonymousUser(), "MyTitle")["queryset"].count(), 0
        )
        self.assertEqual(
            search_resources(AnonymousUser(), "OtherTitle")["queryset"].count(), 0
        )

    @authenticate
    def test_search_on_resources_public_data(self):
        ResourceFactory.create(title="MyTitle", state="public")
        self.assertEqual(
            search_resources(authenticate.user, "MyTitle")["queryset"].count(), 1
        )
        self.assertEqual(
            search_resources(authenticate.user, "OtherTitle")["queryset"].count(), 0
        )

    @authenticate
    def test_search_on_resources_own_private_data(self):
        ResourceFactory.create(
            title="MyTitle", state="private", creator=authenticate.user
        )
        self.assertEqual(
            search_resources(authenticate.user, "MyTitle")["queryset"].count(), 1
        )
        self.assertEqual(
            search_resources(authenticate.user, "OtherTitle")["queryset"].count(), 0
        )

    @authenticate
    def test_search_on_resources_others_private_data(self):
        ResourceFactory.create(title="MyTitle", state="private")
        self.assertEqual(
            search_resources(authenticate.user, "MyTitle")["queryset"].count(), 0
        )
        self.assertEqual(
            search_resources(authenticate.user, "OtherTitle")["queryset"].count(), 0
        )

    def test_anonymous_search_on_bases_public_data(self):
        BaseFactory.create(title="MyTitle", state="public")
        self.assertEqual(
            search_bases(AnonymousUser(), "MyTitle")["queryset"].count(), 1
        )
        self.assertEqual(
            search_bases(AnonymousUser(), "OtherTitle")["queryset"].count(), 0
        )

    def test_anonymous_search_on_bases_private_data(self):
        BaseFactory.create(title="MyTitle", state="private")
        self.assertEqual(
            search_bases(AnonymousUser(), "MyTitle")["queryset"].count(), 0
        )
        self.assertEqual(
            search_bases(AnonymousUser(), "OtherTitle")["queryset"].count(), 0
        )

    @authenticate
    def test_search_on_bases_public_data(self):
        BaseFactory.create(title="MyTitle", state="public")
        self.assertEqual(
            search_bases(authenticate.user, "MyTitle")["queryset"].count(), 1
        )
        self.assertEqual(
            search_bases(authenticate.user, "OtherTitle")["queryset"].count(), 0
        )

    @authenticate
    def test_search_on_bases_own_private_data(self):
        BaseFactory.create(title="MyTitle", state="private", owner=authenticate.user)
        self.assertEqual(
            search_bases(authenticate.user, "MyTitle")["queryset"].count(), 1
        )
        self.assertEqual(
            search_bases(authenticate.user, "OtherTitle")["queryset"].count(), 0
        )

    @authenticate
    def test_search_on_bases_others_private_data(self):
        BaseFactory.create(title="MyTitle", state="private")
        self.assertEqual(
            search_bases(authenticate.user, "MyTitle")["queryset"].count(), 0
        )
        self.assertEqual(
            search_bases(authenticate.user, "OtherTitle")["queryset"].count(), 0
        )

    def test_search_on_resources_multiple_fields(self):
        ResourceFactory.create(title="MyTitle", description="my description")
        self.assertEqual(
            search_resources(authenticate.user, "description")["queryset"].count(), 1
        )
        self.assertEqual(
            search_resources(authenticate.user, "MyTitle")["queryset"].count(), 1
        )

    def test_search_ignores_case(self):
        ResourceFactory.create(title="MyTitle", state="public")
        self.assertEqual(
            search_resources(AnonymousUser(), "MyTitle")["queryset"].count(), 1
        )
        self.assertEqual(
            search_resources(AnonymousUser(), "mytitle")["queryset"].count(), 1
        )

    def test_possible_tags(self):
        tag = TagFactory.create()
        resource = ResourceFactory.create(title="MyTitle", state="public")
        self.assertListEqual(
            list(search_resources(AnonymousUser(), "MyTitle")["possible_tags"]), []
        )

        resource.tags.add(tag)
        self.assertListEqual(
            list(search_resources(AnonymousUser(), "MyTitle")["possible_tags"]),
            [tag.pk],
        )

    def test_search_ressources_restricted(self):
        resource = ResourceFactory.create(title="MyTitle", state="public")
        ResourceFactory.create(title="OtherTitle", state="public")
        self.assertEqual(
            search_resources(
                AnonymousUser(), "MyTitle", restrict_to_base_id=resource.root_base.pk
            )["queryset"].count(),
            1,
        )
        self.assertEqual(
            search_resources(
                AnonymousUser(), "OtherTitle", restrict_to_base_id=resource.root_base.pk
            )["queryset"].count(),
            0,
        )
        self.assertEqual(
            search_resources(
                AnonymousUser(), "", restrict_to_base_id=resource.root_base.pk
            )["queryset"].count(),
            1,
        )

    def test_order_by(self):
        r1: Resource = ResourceFactory.create(state="public")
        r2: Resource = ResourceFactory.create(state="public")
        self.assertEqual(
            search_resources(AnonymousUser(), "", order_by="-modified")[
                "queryset"
            ].count(),
            2,
        )
        # newest resource first
        self.assertEqual(
            search_resources(AnonymousUser(), "", order_by="-modified")["queryset"]
            .first()
            .title,
            r2.title,
        )

        # after updating oldest resources, its the first result
        r1.title = "new title"
        r1.save()
        self.assertEqual(
            search_resources(AnonymousUser(), "", order_by="-modified")["queryset"]
            .first()
            .title,
            "new title",
        )

        # when ordering by -created, last modification does not change the result
        self.assertEqual(
            search_resources(AnonymousUser(), "", order_by="-created")["queryset"]
            .first()
            .title,
            r2.title,
        )


class TestSearchView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("search-list")

    def test_search_view(self):
        tag = TagFactory.create()
        resource = ResourceFactory.create(title="MyTitle", state="public")
        res = self.client.post(
            self.url,
            {"data_type": "resources", "text": "MyTitle"},
            content_type="application/json",
        )
        self.assertListEqual(res.json()["results"]["possibleTags"], [])

        resource.tags.add(tag)
        res = self.client.post(
            self.url,
            {"data_type": "resources", "text": "MyTitle"},
            content_type="application/json",
        )
        self.assertListEqual(res.json()["results"]["possibleTags"], [tag.pk])

    def test_pagination(self):
        base = BaseFactory.create(state="public")
        page_size = SearchView.pagination_class.page_size
        for ix in range(page_size + 1):
            ResourceFactory.create(
                title=f"Resource {ix}", state="public", root_base=base
            )
        # page 1 is limited to page_size results
        res = self.client.post(
            f"{self.url}?page=1",
            {"data_type": "resources", "text": "Resource"},
            content_type="application/json",
        )
        self.assertEqual(res.json()["count"], page_size + 1)
        self.assertEqual(len(res.json()["results"]["objects"]), page_size)

        # page 2 only has one itme
        res = self.client.post(
            f"{self.url}?page=2",
            {"data_type": "resources", "text": "Resource"},
            content_type="application/json",
        )
        self.assertEqual(res.json()["count"], page_size + 1)
        self.assertEqual(len(res.json()["results"]["objects"]), 1)

        # also works without specifying the page
        res = self.client.post(
            f"{self.url}",
            {"data_type": "resources", "text": "Resource"},
            content_type="application/json",
        )
        self.assertEqual(res.json()["count"], page_size + 1)
        self.assertEqual(
            len(res.json()["results"]["objects"]),
            StandardResultsSetPagination.page_size,
        )
