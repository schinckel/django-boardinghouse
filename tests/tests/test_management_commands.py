import json
import sys
import unittest

from contextlib import contextmanager
from cStringIO import StringIO

import django
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection, DatabaseError
from django.db import transaction
from django.test import TestCase

from boardinghouse.schema import get_active_schema, get_schema_model

from ..models import AwareModel, NaiveModel

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
    def test_invalid_schema_causes_error(self):
        with self.assertRaises(CommandError):
            call_command('loaddata', 'foo', schema='foo')

    def test_loading_schemata_creates_pg_schemata(self):
        self.assertEquals(0, Schema.objects.count())
        # Need to use commit=False, else the data will be in a different transaction.
        with capture(call_command, 'loaddata', 'tests/fixtures/schemata.json', commit=False) as output:
            self.assertEquals('Installed 2 object(s) from 1 fixture(s)\n', output)
        self.assertEquals(2, Schema.objects.count())
        Schema.objects.all()[0].activate()
        self.assertTrue(get_active_schema())
        cursor = connection.cursor()
        for schema in Schema.objects.all():
            cursor.execute(SCHEMA_QUERY, [schema.schema])
            data = cursor.fetchone()
            self.assertEquals((schema.schema,), data)
        cursor.close()

    def test_loading_naive_data_does_not_require_schema_arg(self):
        with capture(call_command, 'loaddata', 'tests/fixtures/naive.json', commit=False) as output:
            self.assertEquals('Installed 2 object(s) from 1 fixture(s)\n', output)
        NaiveModel.objects.get(name="naive1")


    def test_loading_naive_data_works_with_schema_passed_in(self):
        Schema.objects.create(name='a', schema='a')
        with capture(call_command, 'loaddata', 'tests/fixtures/naive.json', schema='a', commit=False) as output:
            self.assertEquals('Installed 2 object(s) from 1 fixture(s)\n', output)
        NaiveModel.objects.get(name="naive1")


    def test_loading_aware_data_without_a_schema_fails(self):
        with self.assertRaises(DatabaseError):
            with capture_err(call_command, 'loaddata', 'tests/fixtures/aware.json', commit=False) as output:
                self.assertIn('DatabaseError: Could not load tests.AwareModel(pk=None): relation "tests_awaremodel" does not exist\n', output)

    def test_loading_aware_data_with_template_schema_fails(self):
        with self.assertRaises(DatabaseError):
            with capture_err(call_command, 'loaddata', 'tests/fixtures/aware.json', schema="__template__", commit=False) as output:
                self.assertIn('DatabaseError: Could not load tests.AwareModel(pk=None): relation "tests_awaremodel" does not exist\n', output)

    def test_loading_aware_data_works(self):
        Schema.objects.mass_create('a', 'b')
        with capture(call_command, 'loaddata', 'tests/fixtures/aware.json', schema='a', commit=False) as output:
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
    def test_invalid_schema_raises_exception(self):
        with self.assertRaises(CommandError):
            call_command('dumpdata', 'tests', schema='foo')


    def test_dumpdata_on_naive_models_does_not_require_schema(self):
        with capture(call_command, 'dumpdata', 'boardinghouse') as output:
            self.assertEquals('[]', output)

    def test_dumpdata_on_aware_model(self):
        Schema.objects.mass_create('a', 'b')
        Schema.objects.get(schema='a').activate()
        AwareModel.objects.create(name='foo')

        def by_model(x):
            return x['model']

        with capture(call_command, 'dumpdata', 'tests', 'boardinghouse', schema='a') as output:
            data = sorted(json.loads(output), key=by_model)

        self.assertEquals(3, len(data))
        self.assertEquals('boardinghouse.schema', data[0]['model'])
        self.assertEquals('boardinghouse.schema', data[1]['model'])
        self.assertEquals({"status": False, "name": "foo"}, data[2]['fields'])


        with capture(call_command, 'dumpdata', 'tests', 'boardinghouse', schema='b') as output:
            data = sorted(json.loads(output), key=by_model)

        self.assertEquals(2, len(data))
        self.assertEquals('boardinghouse.schema', data[0]['model'])
        self.assertEquals('boardinghouse.schema', data[1]['model'])

    def test_dumpdata_on_aware_model_requires_schema(self):
        with self.assertRaises(CommandError):
            call_command('dumpdata', 'tests.awaremodel')

