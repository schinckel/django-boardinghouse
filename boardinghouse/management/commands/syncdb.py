import os.path

from django.core.management.commands import syncdb
from django.db import models, connection, transaction

try:
    from south.management.commands import syncdb
except ImportError:
    pass

from ...models import Schema, template_schema
from ...schema import _install_clone_schema_function

class Command(syncdb.Command):
    def handle_noargs(self, **options):
        # Ensure we have the clone_schema() function
        _install_clone_schema_function()
        
        # Ensure we have a __template__ schema.
        template_schema.create_schema()
        
        # Set the search path, so we find created models correctly
        cursor = connection.cursor()
        cursor.execute("SET search_path TO public,__template__;")
        cursor.close()
        
        super(Command, self).handle_noargs(**options)
        
        # Ensure all existing schemata exist (in case they were created using RAW SQL or something, as loaddata creates any that are missing).
        for schema in Schema.objects.all():
            schema.create_schema()