"""
Script qui peut être utilisé pour importer l'index de production
avec un fichier json et générer de la donnée locale aléatoire.
"""

import json
from random import shuffle

from tqdm import tqdm

from main.models import TagCategory, Tag, Resource
from main.factories import UserFactory, BaseFactory, ResourceFactory

# generate random data
for i in tqdm(range(50)):
    u = UserFactory.create()
    for _ in range(3):
        b = BaseFactory.create(owner=u)
        for _ in range(10):
            r = ResourceFactory.create(root_base=b)


def to_camel_case(snake_str):
    components = snake_str.split("_")
    # We capitalize the first letter of each component except the first one
    # with the 'title' method and join them together.
    return components[0] + "".join(x.title() for x in components[1:])


with open("/home/maxime/temp/moine.json") as fh:
    index = json.load(fh)

category_fields = [
    "accepts_free_tags",
    "is_draft",
    "name",
    "maximum_tag_count",
    "relates_to",
    "required_to_be_public",
    "slug",
]

tag_fields = ["id", "name", "is_free", "is_draft", "definition", "parent_tag"]

for category in index:
    cat = TagCategory.objects.create(
        **{field: category[to_camel_case(field)] for field in category_fields}
    )
    for tag in category["tags"]:
        Tag.objects.create(
            category=cat, **{field: tag[to_camel_case(field)] for field in tag_fields}
        )

tags = list(Tag.objects.all())

for r in tqdm(Resource.objects.all()):
    shuffle(tags)
    for tag in tags[:10]:
        r.tags.add(tag)
