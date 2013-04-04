from django.db import models
from .models import Schema

def get_schema():
    cursor = models.connection.cursor()
    cursor.execute('SHOW search_path')
    search_path = cursor.fetchone()[0]
    return Schema.objects.get(schema=search_path.split(',')[0])
