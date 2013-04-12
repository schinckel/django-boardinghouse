from django.db import models

from ..base import SchemaAwareModel, MultiSchemaManager

class AwareModel(SchemaAwareModel):
    name = models.CharField(max_length=10, unique=True)
    status = models.BooleanField(default=False)
    
    objects = MultiSchemaManager()
    
    class Meta:
        app_label = 'multi_schema'

class NaiveModel(models.Model):
    name = models.CharField(max_length=10, unique=True)
    status = models.BooleanField(default=False)
    
    class Meta:
        app_label = 'multi_schema'