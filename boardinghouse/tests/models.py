from django.conf import settings
from django.contrib.auth.models import User
from django.db import models

from ..base import SharedSchemaModel, MultiSchemaManager

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


# The existence of this model, although it may not have tests
# that apply to it, is enough to trigger infinite recursion if
# a check for self-referencing models is not made in is_shared_model()
class SelfReferentialModel(models.Model):
    name = models.CharField(max_length=10, unique=True)
    parent = models.ForeignKey('boardinghouse.SelfReferentialModel', related_name='children', null=True, blank=True)
    
    class Meta:
        app_label = 'boardinghouse'
