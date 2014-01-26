"""
"""
from django.db import models

from .models import Schema
from .schema import get_schema

class MultiSchemaMixin(object):
    """
    A mixin that allows for fetching objects from multiple
    schemata in the one request.
    
    Consider this experimental.
    
    .. note:: You probably don't want want this on your QuerySet, just
        on your Manager.
    """
    def from_schemata(self, *schemata):
        """
        Perform these queries across several schemata.
        """
        qs = getattr(self, 'get_queryset', self.get_query_set)()
        query = str(qs.query)
        
        if len(schemata) == 1 and hasattr(schemata[0], 'filter'):
            schemata = schemata[0]

        # We want to fetch all objects from selected schemata.
        # We need to inject the schema as an attribute _schema on the query,
        # so we can access it later.
        multi_query = [
            query.replace(
                'SELECT ', "SELECT '%s' as _schema, "  % schema.schema
            ).replace(
                'FROM "', 'FROM "%s"."' % schema.schema
            ) for schema in schemata
        ]
        
        return self.raw(" UNION ALL ".join(multi_query))

class MultiSchemaManager(MultiSchemaMixin, models.Manager):
    """
    A Manager that allows for fetching objects from multiple schemata
    in the one request.
    """

class SchemaAware(object):
    """
    A mixin that tags an object as schema aware.
    """
    _is_schema_aware = True

class SchemaAwareModel(SchemaAware, models.Model):
    """
    The Base class for models that should be in a seperate schema.
    
    You could just put `_is_schema_aware = True` on your model class, but
    then you would also need to override __eq__ to get correct behaviour
    related to objects from different schemata.
    """

    class Meta:
        abstract = True
    
    def __eq__(self, other):
        return super(SchemaAwareModel, self).__eq__(other) and self._schema == other._schema


def inject_schema_attribute(sender, instance, **kwargs):
    """
    A signal listener that injects the current schema on the object
    just after it is instantiated.
    
    You may use this in conjunction with :class:`MultiSchemaMixin`, it will
    respect any value that has already been set on the instance.
    """
    if not sender._is_schema_aware:
        return
    if not getattr(instance, '_schema', None):
        instance._schema = get_schema()

models.signals.post_init.connect(inject_schema_attribute)