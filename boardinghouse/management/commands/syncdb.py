"""

"""
import os.path

from django.core.management.commands import syncdb
from django.db import models, connection, transaction

try:
    from south.management.commands import syncdb
except ImportError:
    pass

from ...schema import get_schema_model, _wrap_command

class Command(syncdb.Command):
    @_wrap_command
    def handle_noargs(self, **options):
        super(Command, self).handle_noargs(**options)
        
        # Ensure all existing schemata exist (in case they were created using RAW SQL or something, as loaddata creates any that are missing).
        for schema in get_schema_model().objects.all():
            schema.create_schema()
