import re
from typing import Union

from django.core import mail
from django.test import TestCase
from django.urls import reverse

from main.factories import BaseFactory
from main.models import Base, Resource
from main.tests.test_utils import authenticate


class TestReports(TestCase):
    def send_report(self, obj: Union[Base, Resource]):
        url = reverse("report")
        self.motive = "Le contenu est osbolète"
        self.description = "Une description"
        res = self.client.post(
            url,
            {
                "id": obj.pk,
                "description": self.description,
                "instanceType": "Base",
                "motive": self.motive,
            },
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        return mail.outbox[0]

    @authenticate
    def test_send_report_authenticated(self):
        base = BaseFactory.create()
        sent_mail = self.send_report(base)
        self.assertTrue(sent_mail.subject.startswith("[La Base - Signalement]"))
        url = re.findall(r"testserver(\/.*\/)", sent_mail.body)[0]

        # make sure admin url exists
        authenticate.user.is_admin = True
        authenticate.user.is_superuser = True
        authenticate.user.save()
        self.assertEqual(self.client.get(url).status_code, 200)

        # make sure the mail content is correct
        self.assertTrue(self.motive in sent_mail.subject)
        self.assertTrue(self.description in sent_mail.body)
        self.assertTrue(authenticate.user.email in sent_mail.body)

    def test_send_report_anonymous(self):
        base = BaseFactory.create()
        sent_mail = self.send_report(base)
        self.assertTrue("utilisateur anonyme" in sent_mail.body)
