import unittest

from django.db import connection, models
from django.test import TestCase

from boardinghouse.schema import get_schema_model, get_template_schema

Schema = get_schema_model()
template_schema = get_template_schema()

COLUMN_SQL = """
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = '%(table_name)s'
AND table_schema = '%(table_schema)s'
AND column_name = '%(column_name)s';
"""


@unittest.skip
class DjangoMigrate(TestCase):
    def assertTableExists(self, table, schema):
        schema.activate()
        self.assertIn(table, connection.introspection.get_table_list(connection.cursor()))

    def assertTableNotExists(self, table, schema):
        schema.activate()
        self.assertNotIn(table, connection.introspection.get_table_list(connection.cursor()))

    def test_create_model(self):
        from django.db import migrations

        operation = migrations.CreateModel("AwareModel", [
            ('id', models.AutoField(primary_key=True)),
            ('status', models.BooleanField(default=False)),
        ])

        project_state = migrations.state.ProjectState()
        new_state = project_state.clone()
        operation.state_forwards('boardinghouse', new_state)

        with connection.schema_editor() as editor:
            operation.database_forwards('boardinghouse', editor, new_state, project_state)

        for schema in Schema.objects.all():
            self.assertTableExists('boardinghouse_awaremodel', schema)

        with connection.schema_editor() as editor:
            operation.database_backwards('boardinghouse', editor, new_state, project_state)

        for schema in Schema.objects.all():
            self.assertTableNotExists('boardinghouse_awaremodel', schema)
