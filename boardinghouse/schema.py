import os

from django.db import models, connection

from .models import Schema, template_schema

def get_schema():
    cursor = connection.cursor()
    cursor.execute('SHOW search_path')
    search_path = cursor.fetchone()[0]
    cursor.close()
    schema_name = search_path.split(',')[0]
    if schema_name == '__template__':
        return template_schema
    try:
        return Schema.objects.get(schema=schema_name)
    except Schema.DoesNotExist:
        return None

def get_schema_or_template():
    schema = get_schema()
    if not schema:
        return '__template__'
    return schema.schema

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