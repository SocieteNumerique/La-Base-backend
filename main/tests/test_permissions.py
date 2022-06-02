from django.contrib.auth.models import AnonymousUser
from django.test import TestCase
from django.urls import reverse

from main.factories import BaseFactory, ResourceFactory, UserFactory
from main.models import RESOURCE_STATE_CHOICES
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

        # test adding a ressource to a base without write access
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
