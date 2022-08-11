import re

from django.core.management import BaseCommand
from django.db import Error

from main.models import Tag
from main.serializers.utils import reset_specific_categories, SPECIFIC_CATEGORY_IDS
from moine_back.settings import BASE_DIR

from csv import DictReader

source_file_path = BASE_DIR / "free_licenses.csv"
reset_specific_categories()
free_license_category_id = SPECIFIC_CATEGORY_IDS["free_license"]


class Command(BaseCommand):
    help = "Import free licenses"

    def add_arguments(self, parser):
        pass

    def import_tags(self, max_n_tags=None):  # noqa: C901
        with open(source_file_path) as fh:
            reader = DictReader(fh, delimiter=",")

            n_tags_created = 0
            n_tags_found = 0

            def n_tags_present():
                return n_tags_found + n_tags_created

            for line in reader:
                if max_n_tags and n_tags_created >= max_n_tags:
                    print(f"already created {max_n_tags} tags")
                    break

                name = line["name"]
                group = line["group"]
                if not name:
                    continue

                if Tag.objects.filter(name=name).exists():
                    tag = Tag.objects.get(name=name)
                    n_tags_found += 1
                    slug_parts = tag.slug.split("_")
                    groups = slug_parts[0].split(",")
                    if group not in groups:
                        tag.slug = f"{slug_parts[0]},{group}_{slug_parts[1]}"[:40]
                        try:
                            tag.save()
                            print(f"tag {name} complété")
                        except Error:
                            print("Error : ", tag, tag.slug, len(tag.slug))
                else:
                    name_slugged = "".join(
                        s.capitalize() for s in re.sub(r"(\s|-)+", "_", name).split("_")
                    )
                    tag = Tag(
                        name=name,
                        definition=line["description"],
                        slug=f"{group}_{n_tags_present():0>2d}{name_slugged}"[:40],
                        category_id=free_license_category_id,
                    )
                    try:
                        tag.save()
                        print(f"tag {name} ajouté")
                        n_tags_created += 1
                    except Error:
                        print("Error : ", tag, tag.slug, len(tag.slug))

            self.stdout.write(
                self.style.SUCCESS(
                    f"{n_tags_present()} tags créés, dont {n_tags_found} déjà présents"
                )
            )

    def handle(self, *args, **options):
        self.import_tags(max_n_tags=None)
