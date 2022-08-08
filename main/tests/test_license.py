import factory
from django.test import TestCase

from django.urls import reverse

from main.factories import (
    TagCategoryFactory,
    TagFactory,
    ResourceFactory,
    TextContentFactory,
    LicenseTextFactory,
)
from main.models import Tag
from main.serializers.utils import reset_specific_categories
from main.tests.test_utils import authenticate


class TestLicenseSerializer(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.license_type_category = TagCategoryFactory.create(
            slug="license_01license", relates_to="Resource,Content"
        )
        cls.free_license_category = TagCategoryFactory.create(
            slug="license_02free", relates_to="Resource,Content"
        )
        cls.access_category = TagCategoryFactory.create(
            slug="license_04access", relates_to="Resource,Content"
        )
        cls.price_category = TagCategoryFactory.create(
            slug="license_00price", relates_to="Resource,Content"
        )
        cls.free_tag = TagFactory(
            category=cls.license_type_category, slug="main_00free"
        )
        cls.proprietary_tag = TagFactory(
            category=cls.license_type_category, slug="main_01proprietary"
        )
        cls.other_tag = TagFactory(
            category=cls.license_type_category, slug="main_02other"
        )
        reset_specific_categories()

    @staticmethod
    def main_test_resource_license(test):
        resource = ResourceFactory.create(
            has_global_license=True, state="public", root_base__owner=authenticate.user
        )
        url = reverse("resource-detail", args=[resource.pk])
        return test(resource, url)

    @staticmethod
    def main_test_content_license(test):
        instance = TextContentFactory.create(
            license_knowledge="specific",
            use_resource_license_and_access=False,
            resource__state="public",
            resource__root_base__owner=authenticate.user,
        )
        url = reverse("content-detail", args=[instance.pk])
        return test(instance, url)

    def set_free_license_data(self, instance):
        license_tags_to_add = [self.free_tag, self.free_license_category.tags.first()]
        access_tags_to_add = {
            self.price_category.tags.first(),
            self.access_category.tags.first(),
        }
        instance.tags.add(*license_tags_to_add, *access_tags_to_add)
        license_tag_ids = {tag.id for tag in license_tags_to_add}
        access_tag_ids = {tag.id for tag in access_tags_to_add}
        return license_tag_ids, access_tag_ids

    def set_and_see_license_data_free(self, instance, get_url):
        license_tag_ids, access_tag_ids = self.set_free_license_data(instance)
        res = self.client.get(get_url)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertSetEqual(set(data["licenseTags"]), license_tag_ids)
        self.assertSetEqual(set(data["accessPriceTags"]), access_tag_ids)
        return data

    def set_and_see_license_data_other(self, instance, get_url):
        license_tags_to_add = [self.other_tag]
        instance.tags.add(*license_tags_to_add)
        license_text = LicenseTextFactory.create(
            name=factory.Faker("text", max_nb_chars=25)
        )
        instance.license_text = license_text
        instance.save()
        license_tag_ids = [tag.id for tag in license_tags_to_add]
        res = self.client.get(get_url)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertSetEqual(set(data["licenseTags"]), set(license_tag_ids))
        self.assertDictEqual(
            data["licenseText"],
            {
                "name": license_text.name,
                "link": license_text.link,
                "file": None,
                "id": license_text.id,
            },
        )
        return data

    @authenticate
    def test_license_free(self):
        self.main_test_content_license(self.set_and_see_license_data_free)
        self.main_test_resource_license(self.set_and_see_license_data_free)
        self.main_test_content_license(self.set_and_see_license_data_other)
        self.main_test_resource_license(self.set_and_see_license_data_other)

    @authenticate
    def test_forgets_license_data_in_resource(self):
        resource = ResourceFactory.create(
            has_global_license=True, state="public", root_base__owner=authenticate.user
        )
        url = reverse("resource-detail", args=[resource.pk])
        res = self.client.patch(
            url, {"hasGlobalLicense": False}, content_type="application/json"
        )
        self.assertEqual(200, res.status_code)
        data = res.json()
        self.assertListEqual(data["licenseTags"], [])
        self.assertListEqual(data["accessPriceTags"], [])

    @authenticate
    def test_forgets_license_data_in_content(self):
        content = TextContentFactory.create(
            license_knowledge="specific",
            use_resource_license_and_access=False,
            resource__state="public",
            resource__root_base__owner=authenticate.user,
        )
        url = reverse("content-detail", args=[content.pk])
        _, access_tag_ids = self.set_free_license_data(content)

        res = self.client.patch(
            url, {"licenseKnowledge": "unknown"}, content_type="application/json"
        )
        self.assertEqual(200, res.status_code)
        data = res.json()
        self.assertListEqual(data["licenseTags"], [])
        self.assertSetEqual(set(data["accessPriceTags"]), access_tag_ids)

    @authenticate
    def test_specific_license_resource_contents_dont_use_resource(self):
        resource = ResourceFactory.create(
            has_global_license=True, state="public", root_base__owner=authenticate.user
        )
        content = TextContentFactory.create(
            license_knowledge="specific",
            use_resource_license_and_access=True,
            resource__state="public",
            resource=resource,
        )
        url_content = reverse("content-detail", args=[content.pk])
        url_resource = reverse("resource-detail", args=[resource.pk])

        res = self.client.patch(
            url_resource, {"hasGlobalLicense": "false"}, content_type="application/json"
        )
        self.assertEqual(200, res.status_code)
        res = self.client.get(url_content)
        self.assertEqual(200, res.status_code)

        data = res.json()
        self.assertFalse(data["useResourceLicenseAndAccess"])

    def no_more_free_forgets_details(self, instance, url, not_free_license_tag_id):
        self.set_and_see_license_data_free(instance, url)
        tags = [tag.id for tag in instance.tags.all() if tag.id != self.free_tag.id]
        tags.append(not_free_license_tag_id)
        free_license_tags_count = instance.tags.filter(
            category_id=self.free_license_category.id
        ).count()
        self.assertNotEqual(free_license_tags_count, 0)

        res = self.client.patch(url, {"tags": tags}, content_type="application/json")
        self.assertEqual(200, res.status_code)
        data = res.json()
        free_license_tags_count = (
            Tag.objects.filter(pk__in=data["tags"])
            .filter(category_id=self.free_license_category.id)
            .count()
        )
        self.assertEqual(free_license_tags_count, 0)

    def free_to_proprietary(self, test):
        return lambda instance, url: test(instance, url, self.proprietary_tag.id)

    def free_to_other(self, test):
        return lambda instance, url: test(instance, url, self.other_tag.id)

    @authenticate
    def test_no_more_free_forgets_details(self):
        self.main_test_content_license(
            self.free_to_proprietary(self.no_more_free_forgets_details)
        )
        self.main_test_resource_license(
            self.free_to_proprietary(self.no_more_free_forgets_details)
        )
        self.main_test_content_license(
            self.free_to_other(self.no_more_free_forgets_details)
        )
        self.main_test_resource_license(
            self.free_to_other(self.no_more_free_forgets_details)
        )

    def to_free_forgets_license_text(self, instance, url):
        self.set_and_see_license_data_other(instance, url)
        tags = [tag.id for tag in instance.tags.all() if tag.id != self.other_tag.id]
        tags.append(self.free_tag.id)
        self.assertIsNotNone(instance.license_text)

        res = self.client.patch(url, {"tags": tags}, content_type="application/json")
        self.assertEqual(200, res.status_code)
        data = res.json()
        self.assertIsNone(data["licenseText"])

    def other_to_proprietary_forgets_license_name(self, instance, url):
        self.set_and_see_license_data_other(instance, url)
        tags = [tag.id for tag in instance.tags.all() if tag.id != self.other_tag.id]
        tags.append(self.proprietary_tag.id)
        self.assertIsNotNone(instance.license_text.name)

        res = self.client.patch(url, {"tags": tags}, content_type="application/json")
        self.assertEqual(200, res.status_code)
        data = res.json()
        self.assertEqual(data["licenseText"]["name"], "")

    @authenticate
    def test_forgets_license_text_data(self):
        self.main_test_content_license(self.to_free_forgets_license_text)
        self.main_test_resource_license(self.to_free_forgets_license_text)
        self.main_test_content_license(self.other_to_proprietary_forgets_license_name)
        self.main_test_resource_license(self.other_to_proprietary_forgets_license_name)
