from django.db import models
from django.contrib.auth.models import User

from ..base import SchemaAwareModel, MultiSchemaManager

User.add_to_class('schemata', models.ManyToManyField(
    'boardinghouse.Schema',
    null=True, blank=True,
    related_name='users',
))

class AwareModel(SchemaAwareModel):
    name = models.CharField(max_length=10, unique=True)
    status = models.BooleanField(default=False)
    
    objects = MultiSchemaManager()
    
    class Meta:
        app_label = 'boardinghouse'

class NaiveModel(models.Model):
    name = models.CharField(max_length=10, unique=True)
    status = models.BooleanField(default=False)
    
    class Meta:
        app_label = 'boardinghouse'