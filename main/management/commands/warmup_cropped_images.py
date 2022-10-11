from django.core.management import BaseCommand
from tqdm import tqdm

from main.models import ResizableImage


class Command(BaseCommand):
    help = "Warm cropped images"

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        for image in tqdm(ResizableImage.objects.all()):
            image.warm_cropping()
