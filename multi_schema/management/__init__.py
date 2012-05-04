from django.db import models, connection
from django.core.management.color import no_style

from multi_schema.models import Schema

def post_syncdb_duplicator(sender, **kwargs):
    # See if any of the newly created models are schema-aware
    schema_aware_models = [m for m in kwargs['created_models'] if m._is_schema_aware and kwargs['app'].__name__ == m.__module__]
    if schema_aware_models:
        import pdb; pdb.set_trace()
        for schema in Schema.objects.all():
            cursor = connection.cursor()
            tables = connection.introspection.table_names()
            known_models = set([model for model in connection.introspection.installed_models(tables)])
            for model in schema_aware_models:
                output, references = connection.creation.sql_create_model(model, no_style(), known_models, schema.schema)
                if output and kwargs.get('verbosity', 0) > 1:
                    print "Creating table %s in schema %s" % (model._meta.db_table, schema.schema)
                for statement in output:
                    cursor.execute(statement)

models.signals.post_syncdb.connect(post_syncdb_duplicator)