from django.core.management import BaseCommand

from main.models import TextBlock
from main.models.text_block import TEXT_BLOCKS


class Command(BaseCommand):
    help = "Create text blocks"

    def handle(self, *args, **options):
        for slug in TEXT_BLOCKS:
            TextBlock.objects.get_or_create(slug=slug, defaults={"content": ""})
