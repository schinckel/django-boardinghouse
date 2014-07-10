from __future__ import unicode_literals

import django
from django.db.backends.postgresql_psycopg2 import base

from .creation import DatabaseCreation

from .schema import DatabaseSchemaEditor

class DatabaseWrapper(base.DatabaseWrapper):
    """
    This is a simple subclass of the Postrges DatabaseWrapper,
    but using our new :class:`DatabaseCreation` class.
    """
    def __init__(self, *args, **kwargs):
        super(DatabaseWrapper, self).__init__(*args, **kwargs)
        self.creation = DatabaseCreation(self)

    def schema_editor(self, *args, **kwargs):
        return DatabaseSchemaEditor(self, *args, **kwargs)