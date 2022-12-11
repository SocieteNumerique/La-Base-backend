from django.test import TestCase
from django.urls import reverse

from main.factories import UserFactory
from main.models import UserSearch
from main.tests.test_utils import authenticate


class TestUserSearch(TestCase):
    @authenticate
    def test_user_search(self):
        list_url = reverse("user_search-list")

        def object_url(pk_):
            return reverse("user_search-detail", args=[pk_])

        # can create UserSearch
        query = "dataType=bases&tags=&page=0"
        res = self.client.post(
            list_url, {"query": query, "data_type": "resources", "name": "new search"}
        )
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()["query"], query)
        pk = res.json()["id"]
        self.assertEqual(UserSearch.objects.get(pk=pk).user, authenticate.user)

        # can list UserSearch
        res = self.client.get(list_url)
        data = res.json()
        self.assertEqual(len(data), 1)

        # can edit UserSearch
        res = self.client.patch(
            object_url(pk),
            {"query": "new_query", "data_type": "bases", "name": "another search"},
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["query"], "new_query")

        # not accessible by another user
        other_user = UserFactory.create()
        self.client.force_login(user=other_user)
        res = self.client.get(list_url)
        data = res.json()
        self.assertEqual(len(data), 0)

        #  can destroy UserSearch
        self.client.force_login(user=authenticate.user)
        res = self.client.delete(object_url(pk))
        self.assertEqual(res.status_code, 204)
        self.assertEqual(UserSearch.objects.count(), 0)
