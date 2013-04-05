import os.path

from django.core.management.commands import syncdb
from django.db import models, connection, transaction

try:
    from south.management.commands import syncdb
except ImportError:
    pass

from ...models import Schema, template_schema

class Command(syncdb.Command):
    def handle_noargs(self, **options):
        # Ensure we have the clone_schema() function
        clone_schema_file = os.path.join(os.path.abspath(__file__ + '/../../../'), 'sql', 'clone_schema.sql')
        clone_schema_function = open(clone_schema_file).readlines()[-1].strip()
        cursor = connection.cursor()
        cursor.execute(clone_schema_function)
        
        # Ensure we have a __template__ schema.
        template_schema.create_schema()
        
        # Set the search path, so we find created models correctly
        cursor = connection.cursor()
        cursor.execute("SET search_path TO public,__template__;")
        
        super(Command, self).handle_noargs(**options)
        
        # Ensure all existing schemata exist (in case we imported them using loaddata or something)
        for schema in Schema.objects.all():
            schema.create_schema()