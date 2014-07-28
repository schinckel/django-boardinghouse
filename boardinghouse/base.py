from __future__ import unicode_literals

"""
"""
from django.db import models


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
        qs = self.get_queryset()
        query = str(qs.query)

        if len(schemata) == 1 and hasattr(schemata[0], 'filter'):
            schemata = schemata[0]

        # We want to fetch all objects from selected schemata.
        # We need to inject the schema as an attribute _schema on the query,
        # so we can access it later.
        multi_query = [
            query.replace(
                'SELECT ', "SELECT '%s' as _schema, " % schema.schema
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


class SharedSchemaMixin(object):
    """
    A Mixin that ensures a subclass will be available in the
    shared schema.
    """
    _is_shared_model = True


class SharedSchemaModel(SharedSchemaMixin, models.Model):
    """
    A Base class for models that should be in the shared schema.

    You should inherit from this class if your model _must_ be in
    the shared schema. Just setting the `_is_shared_model` attribute
    will not be picked up for migrations.
    """

    class Meta:
        abstract = True
