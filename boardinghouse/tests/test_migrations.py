import unittest

import django
from django.conf import settings
from django.db import connection, models
from django.test import TestCase

if django.VERSION < (1,7):
    try:
        from south.db import db
    except ImportError:
        db = None
else:
    from django.db import migrations
    db = None

from ..schema import get_schema_model, get_template_schema, activate_template_schema
from .models import AwareModel

Schema = get_schema_model()
template_schema = get_template_schema()

COLUMN_SQL = """
SELECT column_name, data_type
FROM information_schema.columns 
WHERE table_name = '%(table_name)s'
AND table_schema = '%(table_schema)s'
AND column_name = '%(column_name)s';
"""

@unittest.skipIf(django.VERSION < (1,7), 'migrate not used with < 1.7')
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
        

@unittest.skipIf(django.VERSION > (1,7), "South migrate not used with 1.7+")
@unittest.skipIf(not db, "South migrate not tested if not installed")
class SouthMigrate(TestCase):
    def test_south_module_imports_correctly(self):
        from boardinghouse.backends.south_backend import DatabaseOperations
        from boardinghouse.management.commands import migrate
    
    def test_add_remove_column_aware(self):
        Schema.objects.mass_create('a', 'b')
        
        Schema.objects.get(name='a').activate()
        AwareModel.objects.create(name='foo')
        
        def build_column_query(schema):
            return COLUMN_SQL % {
                'column_name': 'test_column',
                'table_name': 'boardinghouse_awaremodel',
                'table_schema': schema.schema
            }

        # Create a new column on awaremodel
        db.add_column('boardinghouse_awaremodel', 'test_column', models.IntegerField(null=True))
        # Check that the column exists on all of the schemata.
        activate_template_schema()
        columns = db.execute(build_column_query(template_schema))
        self.assertEquals([('test_column', 'integer')], columns)
        for schema in Schema.objects.all():
            schema.activate()
            columns = db.execute(build_column_query(schema))
            self.assertEquals([('test_column', 'integer')], columns)
        
        # add a unique
        db.create_unique('boardinghouse_awaremodel', ['test_column'])
        unique_constraint = 'boardinghouse_awaremodel_test_column_uniq'
        activate_template_schema()
        constraints = list(db._constraints_affecting_columns('boardinghouse_awaremodel', ['test_column']))
        self.assertIn(unique_constraint, constraints)
        for schema in Schema.objects.all():
            schema.activate()
            constraints = db._constraints_affecting_columns('boardinghouse_awaremodel', ['test_column'])
            self.assertIn(unique_constraint, constraints)
        
        # remove the unique
        db.delete_unique('boardinghouse_awaremodel', ['test_column'])
        activate_template_schema()
        constraints = list(db._constraints_affecting_columns('boardinghouse_awaremodel', ['test_column']))
        self.assertNotIn(unique_constraint, constraints)
        for schema in Schema.objects.all():
            schema.activate()
            constraints = db._constraints_affecting_columns('boardinghouse_awaremodel', ['test_column'])
            self.assertNotIn(unique_constraint, constraints)
        
        # alter the column type
        db.alter_column('boardinghouse_awaremodel', 'test_column', models.TextField(null=True))
        activate_template_schema()
        columns = db.execute(build_column_query(template_schema))
        self.assertEquals([('test_column', 'text')], columns)
        for schema in Schema.objects.all():
            schema.activate()
            columns = db.execute(build_column_query(schema))
            self.assertEquals([('test_column', 'text')], columns)
                
        # Remove that column
        db.drop_column('boardinghouse_awaremodel', 'test_column')
        # Check that the column no longer exists on all of the schemata.        
        activate_template_schema()
        columns = db.execute(build_column_query(template_schema))
        self.assertEquals([], columns)
        for schema in Schema.objects.all():
            schema.activate()
            columns = db.execute(build_column_query(schema))
            self.assertEquals([], columns)
        
    def test_table_operations(self):
        Schema.objects.mass_create('a', 'b')
        schemata = list(Schema.objects.all()) + [template_schema]
        
        fields = (
            ('id', models.AutoField(primary_key=True)),
            ('field1', models.IntegerField()),
            ('field2', models.IntegerField()),
        )
        field_names = sorted([(field[0],) for field in fields])
        test_table_sql = "SELECT column_name FROM information_schema.columns WHERE table_name='boardinghouse_awaremodel' AND table_schema='%s'"
        
        # To test create, we need to actually delete first. Our migration
        # handling code will only repeat create actions if the table name
        # matches that of an aware model.
        db.delete_table('boardinghouse_awaremodel')
        for schema in schemata:
            columns = sorted(db.execute(test_table_sql % schema.schema))
            self.assertEquals([], columns)        
        
        db.create_table('boardinghouse_awaremodel', fields)
        # Ensure the table has been created in the template_schema,
        # and all other schemata.
        for schema in schemata:
            columns = sorted(db.execute(test_table_sql % schema.schema))
            self.assertEquals(field_names, columns)
    
    def test_clear_table(self):
        a = Schema.objects.create(name='a', schema='a')
        a.activate()
        
        AwareModel.objects.create(name='foo')
        AwareModel.objects.create(name='bar')
        
        b = Schema.objects.create(name='b', schema='b')
        b.activate()

        AwareModel.objects.create(name='foo')
        AwareModel.objects.create(name='bar')
        
        db.clear_table('boardinghouse_awaremodel')
        
        for schema in Schema.objects.all():
            schema.activate()
            self.assertEquals(0, AwareModel.objects.count())

    
    def test_add_column_with_check(self):
        Schema.objects.mass_create('a', 'b')
        
        db.add_column(
            'boardinghouse_awaremodel', 
            'test_column', 
            models.PositiveSmallIntegerField(default=1, db_index=True),
            keep_default=False
        )
        
        cursor = connection.cursor()

        for schema in Schema.objects.all():
            cursor.execute(COLUMN_SQL % {
                'column_name': 'test_column',
                'table_name': 'boardinghouse_awaremodel',
                'table_schema': schema.schema
            })
            self.assertEquals(('test_column', 'smallint'), cursor.fetchone())

        schema = template_schema
        cursor.execute(COLUMN_SQL % {
            'column_name': 'test_column',
            'table_name': 'boardinghouse_awaremodel',
            'table_schema': '__template__'
        })
        self.assertEquals(('test_column', 'smallint'), cursor.fetchone())
        
        db.add_column(
            'boardinghouse_naivemodel', 
            'test_column', 
            models.PositiveSmallIntegerField(default=1, db_index=True),
            keep_default=False
        )
        
        cursor.execute(COLUMN_SQL % {
            'column_name': 'test_column',
            'table_name': 'boardinghouse_naivemodel',
            'table_schema': 'public'
        })
        self.assertEquals(('test_column', 'smallint'), cursor.fetchone())
    
    def test_add_remove_column_naive(self):
        Schema.objects.mass_create('a','b')
        
        column_sql = COLUMN_SQL % {
            'column_name': 'test_column',
            'table_name': 'boardinghouse_naivemodel',
            'table_schema': 'public',
        }
        
        db.add_column('boardinghouse_naivemodel', 'test_column', models.IntegerField(null=True))
        
        cursor = connection.cursor()
        cursor.execute(column_sql)
        self.assertEquals(('test_column','integer'), cursor.fetchone())        
        
        db.alter_column('boardinghouse_naivemodel', 'test_column', models.TextField(null=True))
        cursor.execute(column_sql)
        self.assertEquals(('test_column','text'), cursor.fetchone())        
        
        db.drop_column('boardinghouse_naivemodel', 'test_column')
        cursor.execute(column_sql)
        self.assertEquals(None, cursor.fetchone())

        cursor.close()
