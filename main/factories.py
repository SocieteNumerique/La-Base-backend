from typing import Optional

from factory.django import DjangoModelFactory
import factory

from main.models import TextContent, ContentSection, Intro
from main.models.user import User
from main.models.models import Collection, LicenseText, Section

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
    description = factory.Faker(
        "sentence",
        nb_words=5,
        locale="fr_FR",
    )
    slug = factory.Faker("text", max_nb_chars=30)

    @factory.post_generation
    def relates_to(self, create, extracted, **kwargs):
        if not extracted:
            return
        if self.relates_to:
            self.relates_to.append(extracted)
        else:
            self.relates_to = [extracted]
        self.save()

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

    @factory.post_generation
    def ignored_duplicates(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            self.ignored_duplicates.add(*extracted)

    @factory.post_generation
    def confirmed_duplicates(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            self.confirmed_duplicates.add(*extracted)


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


class IntroFactory(DjangoModelFactory):
    class Meta:
        model = Intro

    title = factory.Faker("text", max_nb_chars=30)
    slug = factory.Faker("text", max_nb_chars=30)
    order = 0
    page = factory.Faker("text", max_nb_chars=30)


class BaseSectionFactory(DjangoModelFactory):
    class Meta:
        model = Section

    title = factory.Faker("text", max_nb_chars=30)
    description = factory.Faker("text", max_nb_chars=30)
    base = factory.SubFactory(BaseFactory)
    position = 0

    @factory.post_generation
    def resources(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            self.resources.add(*extracted)

    @factory.post_generation
    def collections(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            self.collections.add(*extracted)
