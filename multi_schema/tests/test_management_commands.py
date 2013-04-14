from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection, DatabaseError
from django.test import TestCase

from ..models import Schema
from ..schema import get_schema

from .models import AwareModel, NaiveModel

SCHEMA_QUERY = "SELECT schema_name FROM information_schema.schemata WHERE schema_name = %s"

class TestLoadData(TestCase):
    def test_invalid_schema_causes_error(self):
        with self.assertRaises(CommandError):
            call_command('loaddata', 'foo', schema='foo')
        
    def test_loading_schemata_creates_pg_schemata(self):
        self.assertEquals(0, Schema.objects.count())
        # Need to use commit=False, else the data will be in a different transaction.
        call_command('loaddata', 'multi_schema/tests/fixtures/schemata.json', commit=False)
        self.assertEquals(2, Schema.objects.count())
        Schema.objects.all()[0].activate()
        self.assertTrue(get_schema())
        for schema in Schema.objects.all():
            cursor = connection.cursor()
            cursor.execute(SCHEMA_QUERY, [schema.schema])
            data = cursor.fetchone()
            self.assertEquals((schema.schema,), data)
            

    def test_loading_naive_data_does_not_require_schema_arg(self):
        call_command('loaddata', 'multi_schema/tests/fixtures/naive.json', commit=False)
        NaiveModel.objects.get(name="naive1")
    
    
    def test_loading_naive_data_works_with_schema_passed_in(self):
        Schema.objects.create(name='a', schema='a')
        call_command('loaddata', 'multi_schema/tests/fixtures/naive.json', schema='a', commit=False)
        NaiveModel.objects.get(name="naive1")
    
    
    def test_loading_aware_data_without_a_schema_fails(self):
        with self.assertRaises(DatabaseError):
            call_command('loaddata', 'multi_schema/tests/fixtures/aware.json', commit=False)
    
    def test_loading_aware_data_works(self):
        Schema.objects.mass_create('a', 'b')
        call_command('loaddata', 'multi_schema/tests/fixtures/aware.json', schema='a', commit=False)
        
        Schema.objects.get(schema='a').activate()
        AwareModel.objects.get(name='aware1')
        
        Schema.objects.get(pk='b').activate()
        self.assertRaises(AwareModel.DoesNotExist, AwareModel.objects.get, name='aware1')