import unittest

import django
from django.db import connection
from django.test import TestCase

from ..models import Schema, template_schema

COLUMN_SQL = """
SELECT column_name, data_type
FROM information_schema.columns 
WHERE table_name = '%(table_name)s' 
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
        query_data = {
            'column_name': 'test_column',
            'table_name': 'boardinghouse_awaremodel'
        }
        column_sql = COLUMN_SQL % query_data

        cursor = connection.cursor()
        
        # Create a new column on awaremodel
        db.add_column('boardinghouse_awaremodel', 'test_column', models.IntegerField(null=True))
        # Check that the column exists on all of the schemata.
        template_schema.activate(cursor)
        cursor.execute(column_sql)
        self.assertEquals(('test_column', 'integer'), cursor.fetchone())
        for schema in Schema.objects.all():
            schema.activate(cursor)
            cursor.execute(column_sql)
            self.assertEquals(('test_column', 'integer'), cursor.fetchone())
        
        # add a unique
        db.create_unique('boardinghouse_awaremodel', ['test_column'])
        unique_constraint = 'boardinghouse_awaremodel_test_column_uniq'
        template_schema.activate(cursor)
        constraints = list(db._constraints_affecting_columns('boardinghouse_awaremodel', ['test_column']))
        self.assertIn(unique_constraint, constraints)
        for schema in Schema.objects.all():
            schema.activate(cursor)
            constraints = db._constraints_affecting_columns('boardinghouse_awaremodel', ['test_column'])
            self.assertIn(unique_constraint, constraints)
        
        # remove the unique
        db.delete_unique('boardinghouse_awaremodel', ['test_column'])
        template_schema.activate(cursor)
        constraints = list(db._constraints_affecting_columns('boardinghouse_awaremodel', ['test_column']))
        self.assertNotIn(unique_constraint, constraints)
        for schema in Schema.objects.all():
            schema.activate(cursor)
            constraints = db._constraints_affecting_columns('boardinghouse_awaremodel', ['test_column'])
            self.assertNotIn(unique_constraint, constraints)
        
        # alter the column type
        db.alter_column('boardinghouse_awaremodel', 'test_column', models.TextField(null=True))
        template_schema.activate(cursor)
        cursor.execute(column_sql)
        self.assertEquals(('test_column', 'text'), cursor.fetchone())
        for schema in Schema.objects.all():
            schema.activate(cursor)
            cursor.execute(column_sql)
            self.assertEquals(('test_column', 'text'), cursor.fetchone())
        
        # Remove that column
        db.drop_column('boardinghouse_awaremodel', 'test_column')
        # Check that the column no longer exists on all of the schemata.        
        template_schema.activate(cursor)
        cursor.execute(column_sql)
        self.assertEquals(None, cursor.fetchone())
        
        for schema in Schema.objects.all():
            schema.activate(cursor)
            cursor.execute(column_sql)
            self.assertEquals(None, cursor.fetchone())
        
        cursor.close()
    
    def test_add_remove_column_naive(self):
        from south.db import db
        from django.db import models
        
        Schema.objects.mass_create('a','b')
        
        column_sql = COLUMN_SQL % {
            'column_name': 'test_column',
            'table_name': 'boardinghouse_naivemodel'
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