from django.core.management import BaseCommand

from ...models import DemoSchema


class Command(BaseCommand):
    """Clean up expired user demos.

    Removes the DemoSchema object, and the associated schema from the db for all
    user demos where the expiry date is in the past.
    """
    def handle(self, **options):
        DemoSchema.objects.expired().delete()
