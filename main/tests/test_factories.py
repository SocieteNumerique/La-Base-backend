from django.test import TestCase

from main.factories import ResourceFactory, BaseFactory, TagCategoryFactory, TagFactory


class CanCreateFactories(TestCase):
    def test_can_create_factories(self):
        BaseFactory.create()
        TagCategoryFactory.create()
        TagFactory.create()
        ResourceFactory.create()
