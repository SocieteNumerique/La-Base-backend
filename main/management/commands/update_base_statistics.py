from django.core.management import BaseCommand
from tqdm import tqdm

from main.models import Base


class Command(BaseCommand):
    help = "Update base statistics"

    def handle(self, *args, **options):
        for base in tqdm(Base.objects.all()):
            base.update_stats()
