from django.db import models

from models import Schema

class MultiSchemaMixin(object):
    def from_schemata(self, *schemata):
        """
        Perform these queries across several schemata.
        """
        qs = getattr(self, 'get_queryset', self.get_query_set)()
        query = str(qs.query)
        
        if len(schemata) == 1 and hasattr(schemata[0], 'filter'):
            schemata = schemata[0]
        
        multi_query = [
            query.replace('FROM "', 'FROM "%s"."' % schema.schema) for schema in schemata
        ]
        
        return self.raw(" UNION ALL ".join(multi_query))

class MultiSchemaManager(MultiSchemaMixin, models.Manager):
    pass

class SchemaAware(object):
    _is_schema_aware = True

class SchemaAwareModel(SchemaAware, models.Model):
    """
    The Base class for models that should be in a seperate schema.
    
    You could just put `_is_schema_aware = True` on your model class, though.
    """

    class Meta:
        abstract = True
