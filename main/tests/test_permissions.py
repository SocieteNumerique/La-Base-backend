from django.contrib.auth.models import AnonymousUser
from django.test import TestCase
from django.urls import reverse

from main.factories import (
    BaseFactory,
    ResourceFactory,
    UserFactory,
    UserGroupFactory,
    TagFactory,
)
from main.models.models import RESOURCE_STATE_CHOICES, ResourceUserGroup
from main.query_changes.permissions import (
    bases_queryset_for_user,
    resources_queryset_for_user,
)
from main.tests.test_utils import authenticate


class TestPermissions(TestCase):
    def test_anonymous_can_access_public_data(self):
        user = AnonymousUser()
        BaseFactory.create(is_public=True)
        self.assertEqual(bases_queryset_for_user(user).count(), 1)
        ResourceFactory.create(is_public=True, is_draft=False)
        self.assertEqual(resources_queryset_for_user(user).count(), 1)

    def test_anonymous_cannot_access_private_data(self):
        user = AnonymousUser()
        BaseFactory.create(is_public=False)
        self.assertEqual(bases_queryset_for_user(user).count(), 0)
        ResourceFactory.create(is_public=False, is_draft=False)
        self.assertEqual(resources_queryset_for_user(user).count(), 0)

    @authenticate
    def test_bases_private_access(self):
        # no access to a private base we're not member of
        base = BaseFactory.create(is_public=False)
        self.assertEqual(bases_queryset_for_user(authenticate.user).count(), 0)

        # access to a private base we're owner of
        base.owner = authenticate.user
        base.save()
        self.assertEqual(bases_queryset_for_user(authenticate.user).count(), 1)

        # access to a private base we're admin of
        base.owner = UserFactory.create()
        base.save()
        base.admins.add(authenticate.user)
        self.assertEqual(bases_queryset_for_user(authenticate.user).count(), 1)

    @authenticate
    def test_resources_private_access(self):
        # no access to a private resource we're not member of
        resource = ResourceFactory.create(is_public=False, is_draft=False)
        self.assertEqual(resources_queryset_for_user(authenticate.user).count(), 0)

        # access to a private database we're not member of
        resource.creator = authenticate.user
        resource.save()
        self.assertEqual(resources_queryset_for_user(authenticate.user).count(), 1)

        # access to a private resource where we're owner of the base
        resource.creator = UserFactory.create()
        resource.save()
        resource.root_base.owner = authenticate.user
        resource.root_base.save()
        self.assertEqual(resources_queryset_for_user(authenticate.user).count(), 1)

        # access to a private resource where we're admin of the base
        resource.root_base.owner = UserFactory.create()
        resource.root_base.save()
        resource.root_base.admins.add(authenticate.user)
        self.assertEqual(resources_queryset_for_user(authenticate.user).count(), 1)

    @authenticate
    def test_resources_write_access(self):
        # test writing when no write access
        resource = ResourceFactory.create(is_public=True, is_draft=False)
        url = reverse("resource-detail", args=[resource.pk])
        data = self.client.get(url).json()
        self.assertEqual(data["canWrite"], False)
        res = self.client.patch(
            url, {"title": "updated title"}, content_type="application/json"
        )
        self.assertEqual(res.status_code, 404)

        # test writing with write access
        resource.creator = authenticate.user
        resource.save()
        data = self.client.get(url).json()
        self.assertEqual(data["canWrite"], True)
        res = self.client.patch(
            url, {"title": "updated title"}, content_type="application/json"
        )
        self.assertEqual(res.status_code, 200)

    @authenticate
    def test_bases_write_access(self):
        base = BaseFactory.create(is_public=True)
        url = reverse("base-detail", args=[base.pk])
        data = self.client.get(url).json()
        self.assertEqual(data["canWrite"], False)
        res = self.client.patch(
            url, {"title": "updated title"}, content_type="application/json"
        )
        self.assertEqual(res.status_code, 404)

        base.owner = authenticate.user
        base.save()
        data = self.client.get(url).json()
        self.assertEqual(data["canWrite"], True)
        res = self.client.patch(
            url, {"title": "updated title"}, content_type="application/json"
        )
        self.assertEqual(res.status_code, 200)

    @authenticate
    def test_can_add_resource_to_base(self):
        new_resource_payload = {
            "title": "updated title",
            "state": RESOURCE_STATE_CHOICES[0][0],
        }

        # test adding a resource to a base without write access
        base = BaseFactory.create(is_public=True)
        url = reverse("resource-list")
        new_resource_payload["root_base"] = base.pk
        res = self.client.post(
            url,
            new_resource_payload,
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 403)

        # test adding a ressource to a base with write access
        base = BaseFactory.create(is_public=True, owner=authenticate.user)
        url = reverse("resource-list")
        new_resource_payload["root_base"] = base.pk
        res = self.client.post(
            url,
            new_resource_payload,
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 201)

    @authenticate
    def test_superusers_can_access_and_change_everything(self):
        authenticate.user.is_superuser = True
        authenticate.user.save()
        base = BaseFactory.create()
        self.assertEqual(bases_queryset_for_user(authenticate.user).count(), 1)
        url = reverse("base-detail", args=[base.pk])
        data = self.client.get(url).json()
        self.assertEqual(data["canWrite"], True)

        resource = ResourceFactory.create()
        self.assertEqual(resources_queryset_for_user(authenticate.user).count(), 1)
        url = reverse("resource-detail", args=[resource.pk])
        data = self.client.get(url).json()
        self.assertEqual(data["canWrite"], True)


class UserGroupTest(TestCase):
    @authenticate
    def test_member_of_group(self):
        resource = ResourceFactory.create(is_public=False, is_draft=False)
        group = UserGroupFactory.create()
        resource_user_group = ResourceUserGroup.objects.create(
            resource=resource, group=group, can_write=False
        )
        self.assertEqual(resources_queryset_for_user(authenticate.user).count(), 0)
        group.users.add(authenticate.user)
        self.assertEqual(resources_queryset_for_user(authenticate.user).count(), 1)

        resource_user_group.can_write = False
        resource_user_group.save()
        url = reverse("resource-detail", args=[resource.pk])
        data = self.client.get(url).json()
        self.assertEqual(data["canWrite"], False)

        resource_user_group.can_write = True
        resource_user_group.save()
        url = reverse("resource-detail", args=[resource.pk])
        data = self.client.get(url).json()
        self.assertEqual(data["canWrite"], True)


class ContributorInBasesTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory.create()
        cls.tag = TagFactory.create()
        cls.user.tags.add(cls.tag)
        cls.base = BaseFactory.create(is_public=False)
        cls.base.contributor_tags.add(cls.tag)

    def login(self):
        self.client.force_login(user=self.user)

    def test_contributor_in_bases(self):
        qs = bases_queryset_for_user(self.user)
        self.assertEqual(qs.count(), 1)
        base_ = qs.first()
        self.assertFalse(base_.can_write)
        self.assertTrue(base_.can_add_resources)

        # test has access to resources
        ResourceFactory.create(root_base=self.base)
        qs = resources_queryset_for_user(self.user)
        self.assertEqual(qs.count(), self.base.resources.count())
        resource = qs.first()
        self.assertTrue(resource.can_write, True)

    def test_get_view_has_can_write_and_add_resources_set(self):
        # test serializer
        self.login()
        url = reverse("base-detail", args=[self.base.pk])
        data = self.client.get(url).json()
        self.assertFalse(data["canWrite"])
        self.assertTrue(data["canAddResources"])

    def test_can_add_resource_view(self):
        self.login()
        new_resource_payload = {
            "title": " title",
            "state": RESOURCE_STATE_CHOICES[0][0],
            "root_base": self.base.pk,
        }

        url = reverse("resource-list")
        res = self.client.post(
            url,
            new_resource_payload,
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 201)

    def test_can_change_resource_view(self):
        self.login()
        resource = ResourceFactory.create(root_base=self.base)
        url = reverse("resource-detail", args=[resource.pk])
        res = self.client.patch(
            url, {"title": "new title"}, content_type="application/json"
        )
        self.assertEqual(res.status_code, 200)

    def test_cannot_change_base(self):
        self.login()
        url = reverse("base-detail", args=[self.base.pk])
        res = self.client.delete(url)
        self.assertIn(res.status_code, [403, 404])
        res = self.client.patch(url, {"title": "title"})
        self.assertIn(res.status_code, [403, 404])
