import unittest
import sys
from cStringIO import StringIO
from contextlib import contextmanager

import django
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection, DatabaseError
from django.db import transaction
from django.test import TestCase

from ..schema import get_schema, get_schema_model

from .models import AwareModel, NaiveModel

Schema = get_schema_model()

SCHEMA_QUERY = "SELECT schema_name FROM information_schema.schemata WHERE schema_name = %s"

@contextmanager
def capture(command, *args, **kwargs):
    out, sys.stdout = sys.stdout, StringIO()
    command(*args, **kwargs)
    sys.stdout.seek(0)
    yield sys.stdout.read()
    sys.stdout = out

@contextmanager
def capture_err(command, *args, **kwargs):
    err, sys.stderr = sys.stderr, StringIO()
    command(*args, **kwargs)
    sys.stderr.seek(0)
    yield sys.stderr.read()
    sys.stderr = err

class TestLoadData(TestCase):
    @unittest.skipIf(django.VERSION < (1,5), "CommandError used here")
    def test_invalid_schema_causes_error(self):
        with self.assertRaises(CommandError):
            call_command('loaddata', 'foo', schema='foo')

    @unittest.skipIf(django.VERSION >= (1,5), "SystemExit used here")
    def test_invalid_schema_causes_error_dj_15(self):
        with self.assertRaises(SystemExit):
            with capture_err(call_command, 'loaddata', 'foo', schema='foo') as output:
                self.assertEquals('Error: No Schema found named "foo"\n', output)
        
    def test_loading_schemata_creates_pg_schemata(self):
        self.assertEquals(0, Schema.objects.count())
        # Need to use commit=False, else the data will be in a different transaction.
        with capture(call_command, 'loaddata', 'boardinghouse/tests/fixtures/schemata.json', commit=False) as output:
            self.assertEquals('Installed 2 object(s) from 1 fixture(s)\n', output)
        self.assertEquals(2, Schema.objects.count())
        Schema.objects.all()[0].activate()
        self.assertTrue(get_schema())
        cursor = connection.cursor()
        for schema in Schema.objects.all():
            cursor.execute(SCHEMA_QUERY, [schema.schema])
            data = cursor.fetchone()
            self.assertEquals((schema.schema,), data)
        cursor.close()

    def test_loading_naive_data_does_not_require_schema_arg(self):
        with capture(call_command, 'loaddata', 'boardinghouse/tests/fixtures/naive.json', commit=False) as output:
            self.assertEquals('Installed 2 object(s) from 1 fixture(s)\n', output)
        NaiveModel.objects.get(name="naive1")
    
    
    def test_loading_naive_data_works_with_schema_passed_in(self):
        Schema.objects.create(name='a', schema='a')
        with capture(call_command, 'loaddata', 'boardinghouse/tests/fixtures/naive.json', schema='a', commit=False) as output:
            self.assertEquals('Installed 2 object(s) from 1 fixture(s)\n', output)
        NaiveModel.objects.get(name="naive1")
    
    
    def test_loading_aware_data_without_a_schema_fails(self):
        with self.assertRaises(DatabaseError):
            with capture_err(call_command, 'loaddata', 'boardinghouse/tests/fixtures/aware.json', commit=False) as output:
                self.assertIn('DatabaseError: Could not load boardinghouse.AwareModel(pk=None): relation "boardinghouse_awaremodel" does not exist\n', output)
    
    def test_loading_aware_data_works(self):
        Schema.objects.mass_create('a', 'b')
        with capture(call_command, 'loaddata', 'boardinghouse/tests/fixtures/aware.json', schema='a', commit=False) as output:
            self.assertEquals('Installed 2 object(s) from 1 fixture(s)\n', output)
        
        Schema.objects.get(schema='a').activate()
        AwareModel.objects.get(name='aware1')
        
        Schema.objects.get(pk='b').activate()
        self.assertRaises(AwareModel.DoesNotExist, AwareModel.objects.get, name='aware1')
    
    @unittest.expectedFailure
    def test_loading_data_containing_schema_data_works(self):
        """
        This one is a fair way off: it would be great to be able to dump
        and load data from multiple schemata at once. I'm thinking the
        loading may be easier:)
        """
        self.assertTrue(False)


class TestDumpData(TestCase):
    @unittest.skipIf(django.VERSION < (1,5), "CommandError used here")
    def test_invalid_schema_raises_exception(self):
        with self.assertRaises(CommandError):
            call_command('dumpdata', 'boardinghouse', schema='foo')

    @unittest.skipIf(django.VERSION >= (1,5), "SystemExit used here")
    def test_invalid_schema_raises_exception_dj_15(self):
        with self.assertRaises(SystemExit):
            with capture_err(call_command, 'dumpdata', 'boardinghouse', schema='foo') as output:
                self.assertEquals('Error: No Schema found named "foo"\n', output)
            
    def test_dumpdata_on_naive_models_does_not_require_schema(self):
        with capture(call_command, 'dumpdata', 'boardinghouse') as output:
            self.assertEquals('[]', output)
    
    def test_dumpdata_on_aware_model(self):
        Schema.objects.mass_create('a', 'b')
        Schema.objects.get(schema='a').activate()
        AwareModel.objects.create(name='foo')
        with capture(call_command, 'dumpdata', 'boardinghouse', schema='a') as output:
            self.assertIn('{"status": false, "name": "foo"}', output)
        with capture(call_command, 'dumpdata', 'boardinghouse', schema='b') as output:
            self.assertNotIn('{"status": false, "name": "foo"}', output)
    
    @unittest.skipIf(django.VERSION < (1,5), "CommandError used here")
    def test_dumpdata_on_aware_model_requires_schema(self):
        with self.assertRaises(CommandError):
            call_command('dumpdata', 'boardinghouse.awaremodel')
        
    @unittest.skipIf(django.VERSION >= (1,5), "SystemExit used here")
    def test_dumpdata_on_aware_model_requires_schema_dj_15(self):
        with self.assertRaises(SystemExit):
            with capture_err(call_command, 'dumpdata', 'boardinghouse.awaremodel') as output:
                self.assertEquals('Error: You must pass a schema when an explicit model is aware.', output)


@unittest.skipIf(django.VERSION > (1,7), "SyncDB not used with django 1.7+")
class TestSyncDB(TestCase):
    fixtures = ['schemata.json']
    
    @unittest.skipIf(django.VERSION < (1,6), "Transaction handling needs to be done differently")
    def test_creating_missing_schemata(self):
        """
        This is a pretty severe edge case: for some reason, we have data
        in our Schemata table, without a matching schema.
        
        Doing a syncdb will always fix this.
        """
        cursor = connection.cursor()
        cursor.execute("INSERT INTO boardinghouse_schema (name, schema, is_active) VALUES ('a', 'a', true)")
        cursor.execute(SCHEMA_QUERY, ['a'])
        self.assertEquals(None, cursor.fetchone())
        
        with capture(call_command, 'syncdb') as output:
            pass
        
        cursor.execute(SCHEMA_QUERY, ['a'])
        data = cursor.fetchone()
        self.assertEquals(('a',), data)
        cursor.close()
    
    def test_no_south_no_error(self):
        "Can't really come up with a way to test this!"


