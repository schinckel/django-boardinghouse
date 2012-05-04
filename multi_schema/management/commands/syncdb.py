from django.core.management.commands import syncdb
from django.db import models, connection, transaction

try:
    from south.management.commands import syncdb
except ImportError:
    pass

class Command(syncdb.Command):
    def handle_noargs(self, **options):
        cursor = connection.cursor()        
        # Ensure we have a __template__ schema.
        cursor.execute("SELECT schema_name FROM information_schema.schemata WHERE schema_name = '__template__';")
        if not cursor.fetchone():
            cursor.execute("CREATE SCHEMA __template__;")
        transaction.commit_unless_managed()
        
        # Set the search path
        cursor.execute("SET search_path TO public,__template__;")
        
        super(Command, self).handle_noargs(**options)