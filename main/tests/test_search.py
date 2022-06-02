from django.contrib.auth.models import AnonymousUser
from django.test import TestCase

from main.factories import ResourceFactory, BaseFactory
from main.search import search_resources, search_bases
from main.tests.test_utils import authenticate


class TestSearch(TestCase):
    def test_anonymous_search_on_resources_public_data(self):
        ResourceFactory.create(title="MyTitle", is_public=True)
        self.assertEqual(search_resources(AnonymousUser(), "MyTitle").count(), 1)
        self.assertEqual(search_resources(AnonymousUser(), "OtherTitle").count(), 0)

    def test_anonymous_search_on_resources_private_data(self):
        ResourceFactory.create(title="MyTitle", is_public=False)
        self.assertEqual(search_resources(AnonymousUser(), "MyTitle").count(), 0)
        self.assertEqual(search_resources(AnonymousUser(), "OtherTitle").count(), 0)

    @authenticate
    def test_search_on_resources_public_data(self):
        ResourceFactory.create(title="MyTitle", is_public=True)
        self.assertEqual(search_resources(authenticate.user, "MyTitle").count(), 1)
        self.assertEqual(search_resources(authenticate.user, "OtherTitle").count(), 0)

    @authenticate
    def test_search_on_resources_own_private_data(self):
        ResourceFactory.create(
            title="MyTitle", is_public=False, creator=authenticate.user
        )
        self.assertEqual(search_resources(authenticate.user, "MyTitle").count(), 1)
        self.assertEqual(search_resources(authenticate.user, "OtherTitle").count(), 0)

    @authenticate
    def test_search_on_resources_others_private_data(self):
        ResourceFactory.create(title="MyTitle", is_public=False)
        self.assertEqual(search_resources(authenticate.user, "MyTitle").count(), 0)
        self.assertEqual(search_resources(authenticate.user, "OtherTitle").count(), 0)

    def test_anonymous_search_on_bases_public_data(self):
        BaseFactory.create(title="MyTitle", is_public=True)
        self.assertEqual(search_bases(AnonymousUser(), "MyTitle").count(), 1)
        self.assertEqual(search_bases(AnonymousUser(), "OtherTitle").count(), 0)

    def test_anonymous_search_on_bases_private_data(self):
        BaseFactory.create(title="MyTitle", is_public=False)
        self.assertEqual(search_bases(AnonymousUser(), "MyTitle").count(), 0)
        self.assertEqual(search_bases(AnonymousUser(), "OtherTitle").count(), 0)

    @authenticate
    def test_search_on_bases_public_data(self):
        BaseFactory.create(title="MyTitle", is_public=True)
        self.assertEqual(search_bases(authenticate.user, "MyTitle").count(), 1)
        self.assertEqual(search_bases(authenticate.user, "OtherTitle").count(), 0)

    @authenticate
    def test_search_on_bases_own_private_data(self):
        BaseFactory.create(title="MyTitle", is_public=False, owner=authenticate.user)
        self.assertEqual(search_bases(authenticate.user, "MyTitle").count(), 1)
        self.assertEqual(search_bases(authenticate.user, "OtherTitle").count(), 0)

    @authenticate
    def test_search_on_bases_others_private_data(self):
        BaseFactory.create(title="MyTitle", is_public=False)
        self.assertEqual(search_bases(authenticate.user, "MyTitle").count(), 0)
        self.assertEqual(search_bases(authenticate.user, "OtherTitle").count(), 0)

    def test_search_on_resources_multiple_fields(self):
        ResourceFactory.create(title="MyTitle", description="my description")
        self.assertEqual(search_resources(authenticate.user, "description").count(), 1)
        self.assertEqual(search_resources(authenticate.user, "MyTitle").count(), 1)

    def test_search_ignores_case(self):
        ResourceFactory.create(title="MyTitle", is_public=True)
        self.assertEqual(search_resources(AnonymousUser(), "MyTitle").count(), 1)
        self.assertEqual(search_resources(AnonymousUser(), "mytitle").count(), 1)
