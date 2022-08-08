from typing import Optional

from factory.django import DjangoModelFactory
import factory

from main.models import TextContent, ContentSection
from main.models.user import User
from main.models.models import Collection, LicenseText

from main.models.models import Tag, TagCategory, Base, Resource
from main.models.user import UserGroup

factory.Faker._DEFAULT_LOCALE = "fr_FR"


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    password: Optional[str] = factory.Faker("password")
    first_name: str = factory.Faker("first_name")
    last_name: str = factory.Faker("last_name")
    email: str = factory.Faker("email")
    is_admin: Optional[bool] = False
    is_active: Optional[bool] = True

    @factory.post_generation
    def set_password(self, create, extracted, **kwargs):
        self.set_password("password")
        self.save()


class BaseFactory(DjangoModelFactory):
    class Meta:
        model = Base

    owner = factory.SubFactory(UserFactory)
    title = factory.Faker("text", max_nb_chars=30)


class TagCategoryFactory(DjangoModelFactory):
    class Meta:
        model = TagCategory

    name = factory.Faker("name", locale="fr_FR")
    description = factory.Faker("paragraph", locale="fr_FR")
    relates_to = "Resource"
    slug = factory.Faker("text", max_nb_chars=30)

    @factory.post_generation
    def create_tags(self, create, extracted, **kwargs):
        for _ in range(5):
            self.tags.add(TagFactory.create(category=self))


class TagFactory(DjangoModelFactory):
    class Meta:
        model = Tag

    name = factory.Faker("text", max_nb_chars=20)
    category = factory.SubFactory(TagCategoryFactory)


class ResourceFactory(DjangoModelFactory):
    class Meta:
        model = Resource

    title = factory.Faker("text", max_nb_chars=30)
    root_base = factory.SubFactory(BaseFactory)
    description = factory.Faker("text", max_nb_chars=60)


class CollectionFactory(DjangoModelFactory):
    class Meta:
        model = Collection

    name = factory.Faker("text", max_nb_chars=25)
    base = factory.SubFactory(BaseFactory)


class UserGroupFactory(DjangoModelFactory):
    class Meta:
        model = UserGroup

    name = factory.Faker("text", max_nb_chars=30)


class LicenseTextFactory(DjangoModelFactory):
    class Meta:
        model = LicenseText
        exclude = ("has_link", "has_name")

    has_link = factory.Faker("boolean")
    has_name = factory.Faker("boolean")
    link = factory.Maybe("has_link", factory.Faker("url"), None)
    name = factory.Maybe("has_link", factory.Faker("text", max_nb_chars=30), None)


def order(nb_built):
    return nb_built + 1


class SectionFactory(DjangoModelFactory):
    class Meta:
        model = ContentSection

    resource = factory.SubFactory(ResourceFactory)
    title = factory.Faker("text", max_nb_chars=30)
    order = factory.Sequence(order)


class TextContentFactory(DjangoModelFactory):
    class Meta:
        model = TextContent

    text = factory.Faker("paragraph")
    title = factory.Faker("text", max_nb_chars=30)
    resource = factory.SubFactory(ResourceFactory)
    is_draft = False
    section = factory.LazyAttribute(lambda o: SectionFactory(resource=o.resource))
    order = factory.Sequence(order)
