from django.db.backends.postgresql_psycopg2.base import DatabaseWrapper as DBW
from django.conf import settings

from creation import DatabaseCreation

class DatabaseWrapper(DBW):
    """
    This is a simple subclass of the Postrges DatabaseWrapper,
    but using our new :class:`DatabaseCreation` class.
    """
    def __init__(self, *args, **kwargs):
        super(DatabaseWrapper, self).__init__(*args, **kwargs)
        self.creation = DatabaseCreation(self)