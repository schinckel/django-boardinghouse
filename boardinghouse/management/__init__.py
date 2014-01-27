from django.db import models, connection
from django.core.management.color import no_style

from boardinghouse.models import Schema
from boardinghouse.schema import is_shared_model

def post_syncdb_duplicator(sender, **kwargs):
    # See if any of the newly created models are schema-aware
    schema_aware_models = [
        m for m in kwargs['created_models'] 
        if not is_shared_model(m) 
        and kwargs['app'].__name__ == m.__module__
    ]
    if schema_aware_models:
        cursor = connection.cursor()
        for schema in Schema.objects.all():
            schema.activate(cursor)
            tables = connection.introspection.table_names()
            pending_references = {}
            known_models = set([
                model for model in connection.introspection.installed_models(tables)
            ])
            seen_models = set(known_models)
            for model in schema_aware_models:
                if model in seen_models:
                    continue
                output, references = connection.creation.sql_create_model(model, no_style(), known_models, schema.schema)
                seen_models.add(model)
                for refto, refs in references.items():
                    pending_references.setdefault(refto, []).extend(refs)
                    if refto in seen_models:
                        output.extend(connection.creation.sql_for_pending_references(refto, no_style(), pending_references))
                output.extend(connection.creation.sql_for_pending_references(model, no_style(), pending_references))
                
                if output and kwargs.get('verbosity', 0) > 1:
                    print " ... creating table %s in schema %s" % (model._meta.db_table, schema.schema)
                for statement in output:
                    cursor.execute(statement)
                tables.append(connection.introspection.table_name_converter(model._meta.db_table))
        cursor.close()

models.signals.post_syncdb.connect(post_syncdb_duplicator)