from django.db import models
from .models import Schema

def get_schema():
    cursor = models.connection.cursor()
    cursor.execute('SHOW search_path')
    search_path = cursor.fetchone()[0]
    try:
        return Schema.objects.get(schema=search_path.split(',')[0])
    except Schema.DoesNotExist:
        return None

def activate_schema(schema):
    Schema.objects.get(schema=schema).activate()

def deactivate_schema(schema=None):
    Schema().deactivate()