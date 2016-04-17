from __future__ import unicode_literals

from django.db.backends.postgresql import base

from .schema import DatabaseSchemaEditor
from .creation import DatabaseCreation


class DatabaseWrapper(base.DatabaseWrapper):
    """
    This is a simple subclass of the Postrges DatabaseWrapper,
    but using our new :class:`DatabaseSchemaEditor` class.
    """
    def __init__(self, *args, **kwargs):
        super(DatabaseWrapper, self).__init__(*args, **kwargs)
        self.creation = DatabaseCreation(self)

    def schema_editor(self, *args, **kwargs):
        return DatabaseSchemaEditor(self, *args, **kwargs)
