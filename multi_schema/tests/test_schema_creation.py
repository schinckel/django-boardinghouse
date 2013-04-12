from django.test import TestCase
from django.db import connection

class TestSchemaCreation(TestCase):
    def test_template_schema_is_created(self):
        cursor = connection.cursor()
        cursor.execute("SELECT nspname FROM pg_namespace WHERE nspname = '__template__'")
        data = cursor.fetchone()
        self.assertEquals(('__template__',), data)