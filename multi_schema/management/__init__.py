from django.db import models

from multi_schema.models import Schema

def post_syncdb_duplicator(sender, **kwargs):
    # See if any of the newly created models are schema-aware
    schema_aware_models = [m for m in kwargs['created_models'] if getattr(m, '_is_schema_aware')]
    if schema_aware_models:
        for schema in Schema.objects.all():
            schema.activate()
            # Now create the models.

models.signals.post_syncdb.connect(post_syncdb_duplicator)