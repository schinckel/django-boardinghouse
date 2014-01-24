import unittest

import django
from django.db import connection
from django.test import TestCase

from ..models import Schema, template_schema
from .models import AwareModel

COLUMN_SQL = """
SELECT column_name, data_type
FROM information_schema.columns 
WHERE table_name = '%(table_name)s'
AND table_schema = '%(table_schema)s'
AND column_name = '%(column_name)s';
"""

@unittest.skipIf(django.VERSION < (1,7), 'migrate not used with < 1.7')
class DjangoMigrate(TestCase):
    pass

@unittest.skipIf(django.VERSION > (1,7), "South migrate not used with 1.7+")
class SouthMigrate(TestCase):
    def test_south_module_imports_correctly(self):
        from boardinghouse.backends.south_backend import DatabaseOperations
    
    def test_add_remove_column_aware(self):
        from south.db import db
        from django.db import models
        
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
        template_schema.activate()
        columns = db.execute(build_column_query(template_schema))
        self.assertEquals([('test_column', 'integer')], columns)
        for schema in Schema.objects.all():
            schema.activate()
            columns = db.execute(build_column_query(schema))
            self.assertEquals([('test_column', 'integer')], columns)
        
        # add a unique
        db.create_unique('boardinghouse_awaremodel', ['test_column'])
        unique_constraint = 'boardinghouse_awaremodel_test_column_uniq'
        template_schema.activate()
        constraints = list(db._constraints_affecting_columns('boardinghouse_awaremodel', ['test_column']))
        self.assertIn(unique_constraint, constraints)
        for schema in Schema.objects.all():
            schema.activate()
            constraints = db._constraints_affecting_columns('boardinghouse_awaremodel', ['test_column'])
            self.assertIn(unique_constraint, constraints)
        
        # remove the unique
        db.delete_unique('boardinghouse_awaremodel', ['test_column'])
        template_schema.activate()
        constraints = list(db._constraints_affecting_columns('boardinghouse_awaremodel', ['test_column']))
        self.assertNotIn(unique_constraint, constraints)
        for schema in Schema.objects.all():
            schema.activate()
            constraints = db._constraints_affecting_columns('boardinghouse_awaremodel', ['test_column'])
            self.assertNotIn(unique_constraint, constraints)
        
        # alter the column type
        db.alter_column('boardinghouse_awaremodel', 'test_column', models.TextField(null=True))
        template_schema.activate()
        columns = db.execute(build_column_query(template_schema))
        self.assertEquals([('test_column', 'text')], columns)
        for schema in Schema.objects.all():
            schema.activate()
            columns = db.execute(build_column_query(schema))
            self.assertEquals([('test_column', 'text')], columns)
        
        # Remove that column
        db.drop_column('boardinghouse_awaremodel', 'test_column')
        # Check that the column no longer exists on all of the schemata.        
        template_schema.activate()
        columns = db.execute(build_column_query(template_schema))
        self.assertEquals([], columns)
        for schema in Schema.objects.all():
            schema.activate()
            columns = db.execute(build_column_query(schema))
            self.assertEquals([], columns)
        
    def test_table_operations(self):
        from south.db import db
        from django.db import models
        
        Schema.objects.mass_create('a', 'b')
        schemata = list(Schema.objects.all()) + [template_schema]
        
        fields = (
            ('id', models.AutoField(primary_key=True)),
            ('field1', models.IntegerField()),
            ('field2', models.IntegerField()),
        )
        field_names = [(field[0],) for field in fields]
        test_table_sql = "SELECT column_name FROM information_schema.columns WHERE table_name='boardinghouse_awaremodel' AND table_schema='%s'"
        
        # To test create, we need to actually delete first, as we check the model's _is_schema_aware attribute!
        db.delete_table('boardinghouse_awaremodel')
        for schema in schemata:
            schema.activate()
            columns = db.execute(test_table_sql % schema.schema)
            self.assertEquals([], columns)        
        
        db.create_table('boardinghouse_awaremodel', fields)
        # Ensure the table has been created in the template_schema,
        # and all other schemata.
        for schema in schemata:
            schema.activate()
            columns = db.execute(test_table_sql % schema.schema)
            self.assertEquals(field_names, columns)
        
        
    def test_add_remove_column_naive(self):
        from south.db import db
        from django.db import models
        
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