from django.core.management.commands import syncdb
from django.db import models, connection, transaction

try:
    from south.management.commands import syncdb
except ImportError:
    pass

class Command(syncdb.Command):
    def handle_noargs(self, **options):
        import pdb; pdb.set_trace()
        # Set the db_table to all non-schema-aware models to public.db_table
        processed_models = []
        for model in models.get_models():
            if getattr(model, '_is_schema_aware', False):
                if not model._meta.db_table.startswith('__template__"."'):
                    model._meta.db_table = '__template__"."' + model._meta.db_table
                    processed_models.append(model)
        
        cursor = connection.cursor()
        
        # Ensure we have a __template__ schema.
        cursor.execute("SELECT schema_name FROM information_schema.schemata WHERE schema_name = '__template__';")
        if not cursor.fetchone():
            cursor.execute("CREATE SCHEMA __template__;")
        
        # Set the search path
        cursor.execute("SET search_path TO public,__template__;")
        
        super(Command, self).handle_noargs(**options)
        
        # reset the search_path
        cursor = connection.cursor()
        cursor.execute("SET search_path to public;")
        transaction.commit_unless_managed()