from django.test import TestCase
from django.urls import reverse

from main.factories import TagCategoryFactory


class TestTagView(TestCase):
    def test_added_tags_are_marked_as_free(self):
        url = reverse("tag-list")
        tag_category = TagCategoryFactory.create()
        res = self.client.post(url, {"name": "My tag", "category": tag_category.pk})
        self.assertEqual(res.json()["isFree"], True)
