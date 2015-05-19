from __future__ import unicode_literals

from django.db.backends.postgresql_psycopg2 import base

from .schema import DatabaseSchemaEditor


class DatabaseWrapper(base.DatabaseWrapper):
    """
    This is a simple subclass of the Postrges DatabaseWrapper,
    but using our new :class:`DatabaseSchemaEditor` class.
    """

    def schema_editor(self, *args, **kwargs):
        return DatabaseSchemaEditor(self, *args, **kwargs)
