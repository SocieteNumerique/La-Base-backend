from django.test import TestCase
from django.urls import reverse

from main.factories import ResourceFactory
from main.models import ContentSection
from main.tests.test_utils import authenticate


class TestResourceView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("content-list")
        cls.resource = ResourceFactory.create()
        cls.section = ContentSection.objects.create(
            resource=cls.resource, title="title", order=0
        )

    @authenticate
    def test_write_text_content(self):
        response = self.client.post(
            self.url,
            {
                "type": "text",
                "text": "",
                "section": self.section.pk,
                "order": 0,
                "resource": self.resource.pk,
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)

    @authenticate
    def test_write_text_content_with_script(self):
        response = self.client.post(
            self.url,
            {
                "type": "text",
                "text": "<strong>Bold text</strong><script>evil script</script>",
                "section": self.section.pk,
                "order": 0,
                "resource": self.resource.pk,
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        text = response.json()["text"]
        self.assertFalse("<script>" in text)
        self.assertTrue("<strong>" in text)
