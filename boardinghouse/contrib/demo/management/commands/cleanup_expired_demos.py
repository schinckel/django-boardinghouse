from django.core.management import BaseCommand

from ...models import DemoSchema


class Command(BaseCommand):
    def handle(self, **options):
        DemoSchema.objects.expired().delete()
