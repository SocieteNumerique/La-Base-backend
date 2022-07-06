import re
from urllib.parse import urlencode

import faker
from django.contrib.auth import authenticate as django_authenticate
from django.test import TestCase
from django.urls import reverse
from django.core import mail

from main.factories import UserFactory, TagFactory, TagCategoryFactory
from main.models.user import User
from main.serializers.user_serializer import CNFS_RESERVED_TAG_NAME, CNFS_EMAIL_DOMAIN
from main.tests.test_utils import authenticate

faker_ = faker.Faker()


def get_standard_user_data(but=None):
    data = {
        "email": faker_.email(),
        "password": faker_.password(),
        "firstName": faker_.first_name(),
        "lastName": faker_.last_name(),
    }
    if but:
        data.pop(but)
    return data


class TestUserView(TestCase):
    def test_can_create_user(self):
        url = reverse("user-list")
        res = self.client.post(
            url,
            get_standard_user_data(),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 201)

    def test_can_create_user_with_tags(self):
        url = reverse("user-list")
        data = get_standard_user_data()
        category = TagCategoryFactory.create(relates_to="User")
        tag = TagFactory.create(category=category)
        data["tags"] = [tag.pk]
        res = self.client.post(
            url,
            data,
            content_type="application/json",
        )
        user = User.objects.get(email=res.json()["email"])
        self.assertEqual(res.status_code, 201)
        self.assertListEqual(res.json()["tags"], [tag.pk])
        self.assertListEqual(
            list(user.tags.all().values_list("pk", flat=True)), [tag.pk]
        )

    def test_cannot_set_cnfs_tag_on_request(self):
        url = reverse("user-list")
        data = get_standard_user_data()
        category = TagCategoryFactory.create(relates_to="User")
        tag = TagFactory.create(category=category, name=CNFS_RESERVED_TAG_NAME)
        data["tags"] = [tag.pk]
        res = self.client.post(
            url,
            data,
            content_type="application/json",
        )
        user = User.objects.get(email=res.json()["email"])
        self.assertEqual(res.status_code, 201)
        self.assertListEqual(res.json()["tags"], [])
        self.assertListEqual(list(user.tags.all().values_list("pk", flat=True)), [])

    def test_cannot_cnfs_tag_is_set_for_special_emails(self):
        url = reverse("user-list")
        data = get_standard_user_data()
        category = TagCategoryFactory.create(relates_to="User")
        cnfs_tag = TagFactory.create(category=category, name=CNFS_RESERVED_TAG_NAME)
        data["email"] = f"{data['email'].split('@')[0]}{CNFS_EMAIL_DOMAIN}"
        res = self.client.post(
            url,
            data,
            content_type="application/json",
        )
        user = User.objects.get(email=res.json()["email"])
        self.assertEqual(res.status_code, 201)
        self.assertListEqual(res.json()["tags"], [cnfs_tag.pk])
        self.assertListEqual(
            list(user.tags.all().values_list("pk", flat=True)), [cnfs_tag.pk]
        )

    def test_cannot_create_user_with_bad_params(self):
        url = reverse("user-list")
        res = self.client.post(
            url,
            dict(**get_standard_user_data(but="email"), email="blabla"),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 400)

        res = self.client.post(
            url,
            dict(**get_standard_user_data(but="password"), password="123"),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 400)

        res = self.client.post(
            url,
            dict(**get_standard_user_data(but="firstName"), firstName=""),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 400)

        res = self.client.post(
            url,
            dict(**get_standard_user_data(but="lastName"), lastName="f"),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 400)

    @authenticate
    def test_can_change_password(self):
        password = faker_.password()
        new_password = faker_.password()
        authenticate.user.set_password(password)
        authenticate.user.save()
        # after password change, we must re-login
        self.client.force_login(user=authenticate.user)
        url = reverse("user-password", args=[authenticate.user.pk])
        res = self.client.patch(
            url,
            dict(newPassword=new_password, oldPassword=password),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200)

        # check password has been changed
        res = django_authenticate(
            self.client.request, email=authenticate.user.email, password=new_password
        )
        self.assertTrue(res)

    def test_can_reset_email(self):
        user = UserFactory.create()
        url = reverse(
            "reset-password",
        )
        self.client.get(f"{url}?email={user.email}")
        self.assertEqual(len(mail.outbox), 1)
        mail_ = mail.outbox[0]
        self.assertTrue(mail_.subject.startswith("Réinitialisation du mot de passe"))

        # get url from mail
        url = re.findall(r"testserver(\/.*\/)", mail_.body)[0]
        res = self.client.get(url, follow=True)
        self.assertEqual(res.status_code, 200)

        # get csrf token from body, fill form and send
        new_password = faker_.password()
        body = res.content.decode()
        csrf_token, email, _ = re.findall('value="(.*)"', body)
        data = urlencode(
            {
                "csrfmiddlewaretoken": csrf_token,
                "new_password1": new_password,
                "new_password2": new_password,
            }
        )
        url = res._request.path
        res = self.client.post(
            url, data, content_type="application/x-www-form-urlencoded", follow=True
        )

        # check password has changed
        user_ = django_authenticate(
            self.client.request, email=user.email, password=new_password
        )
        self.assertEqual(user_, user)

    def test_user_activation(self):
        # create user from view
        url = reverse("user-list")
        res = self.client.post(
            url,
            get_standard_user_data(),
            content_type="application/json",
        )
        user = User.objects.get()
        self.assertFalse(user.is_active)

        self.assertEqual(len(mail.outbox), 1)
        mail_ = mail.outbox[0]

        # get url from mail
        url = re.findall(r"testserver(\/.*\/)", mail_.body)[0]
        # click on url
        res = self.client.get(url)
        self.assertEqual(res.status_code, 302)
        self.assertTrue(User.objects.get().is_active)
