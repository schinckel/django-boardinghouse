from django.core.management import NoArgsCommand

from ..models import DemoSchema


class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        DemoSchema.objects.expired().delete()
