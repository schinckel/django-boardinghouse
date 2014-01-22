import os

from django.db import models, connection

from .models import Schema

def get_schema():
    cursor = connection.cursor()
    cursor.execute('SHOW search_path')
    search_path = cursor.fetchone()[0]
    cursor.close()
    try:
        return Schema.objects.get(schema=search_path.split(',')[0])
    except Schema.DoesNotExist:
        return None

def activate_schema(schema):
    Schema.objects.get(schema=schema).activate()

def deactivate_schema(schema=None):
    Schema().deactivate()


def _install_clone_schema_function():
    clone_schema_file = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'sql', 'clone_schema.sql')
    clone_schema_function = " ".join([x.strip() for x in open(clone_schema_file).readlines() if not x.strip().startswith('--')])
    clone_schema_function = clone_schema_function.replace("%", "%%")
    cursor = connection.cursor()
    cursor.execute(clone_schema_function)
    cursor.close()