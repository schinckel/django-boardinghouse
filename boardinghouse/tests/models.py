from django.conf import settings
from django.contrib.auth.models import User
from django.db import models

from ..base import SharedSchemaModel, MultiSchemaManager

User.add_to_class('schemata', models.ManyToManyField(
    'boardinghouse.schema',
    null=True, blank=True,
    related_name='users',
))

class AwareModel(models.Model):
    name = models.CharField(max_length=10, unique=True)
    status = models.BooleanField(default=False)
    
    objects = MultiSchemaManager()
    
    class Meta:
        app_label = 'boardinghouse'

class NaiveModel(SharedSchemaModel):
    name = models.CharField(max_length=10, unique=True)
    status = models.BooleanField(default=False)
    
    class Meta:
        app_label = 'boardinghouse'