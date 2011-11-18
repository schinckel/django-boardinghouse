from django.conf import settings
from django.contrib.auth.models import User
from django.db import models, connection

class Schema(models.Model):
    name = models.CharField(max_length=128)
    schema = models.CharField(max_length=36)
    
    class Meta:
        app_label = 'multi_schema'
    
    def __unicode__(self):
        return self.name
        
try:
    User._meta.get_field_by_name('schema')
except:
    User.add_to_class('schema', models.ForeignKey(Schema, null=True, blank=True))


class SchemaAwareModel(models.Model):
    """
    This is an abstract base class that will ensure any requests hit the schema,
    """
    class Meta:
        abstract = True

class Person(SchemaAwareModel):
    user = models.ForeignKey(User)
    date_of_birth = models.DateField()