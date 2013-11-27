from django.db.backends.postgresql_psycopg2.base import DatabaseWrapper as DBW
from django.conf import settings

from creation import DatabaseCreation

class DatabaseWrapper(DBW):
    def __init__(self, *args, **kwargs):
        super(DatabaseWrapper, self).__init__(*args, **kwargs)
        self.creation = DatabaseCreation(self)