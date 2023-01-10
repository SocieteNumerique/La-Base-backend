import re

from django.core import mail
from django.test import TestCase
from django.urls import reverse

from main.factories import ResourceFactory, BaseFactory
from main.tests.test_utils import authenticate

contributions = {
    "contributor": {
        "body": "ajouter en contributeur",
    },
    "suggestion": {
        "body": "a une suggestion à faire",
    },
}


class TestTagView(TestCase):
    @authenticate
    def test_can_contribute(self):
        resource = ResourceFactory.create(state="public")
        url = reverse("contribute")
        for ix, (contribute_choice, value) in enumerate(contributions.items(), start=1):
            res = self.client.post(
                url,
                {
                    "id": resource.id,
                    "message": "MY_MESSAGE",
                    "contribute_choice": contribute_choice,
                },
            )
            self.assertEqual(res.status_code, 200)
            self.assertEqual(len(mail.outbox), ix)
            mail_ = mail.outbox[ix - 1]
            self.assertTrue("Suggestion d’un utilisateur" in mail_.subject)
            self.assertTrue("MY_MESSAGE" in mail_.body)
            self.assertTrue(value["body"] in mail_.body)
            self.assertTrue(authenticate.user.email in mail_.body)
            self.assertListEqual(mail_.to, [resource.root_base.owner.email])

    @authenticate
    def test_can_transfer_resource(self):
        resource = ResourceFactory.create(state="public")
        target_base = BaseFactory.create(owner=authenticate.user)

        url = reverse("contribute")
        res = self.client.post(
            url,
            {
                "id": resource.id,
                "message": "MY_MESSAGE",
                "target_base": target_base.pk,
                "contribute_choice": "administrator",
            },
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        mail_ = mail.outbox[0]
        self.assertTrue("Suggestion d’un utilisateur" in mail_.subject)
        self.assertTrue("MY_MESSAGE" in mail_.body)

        # get url from mail
        url = re.findall(r"testserver(\/.*\/)", mail_.body)[0]
        self.assertTrue("transfer" in url)

        # test clicking on link as not resource owner does not work
        res = self.client.get(url, follow=True)
        self.assertEqual(res.status_code, 403)

        # click on link as resource owner
        self.client.force_login(user=resource.root_base.owner)
        res = self.client.get(url, follow=True)
        self.assertEqual(res.status_code, 200)
        resource.refresh_from_db()
        self.assertEqual(resource.root_base, target_base)
