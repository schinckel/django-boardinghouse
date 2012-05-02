from django.conf import settings
from django.contrib.auth.models import User
from django.db import models, connection

models.Model._is_schema_aware = False

class Schema(models.Model):
    name = models.CharField(max_length=128)
    schema = models.CharField(max_length=36)
    
    class Meta:
        app_label = 'multi_schema'
    
    def __unicode__(self):
        return self.name
    
    def create_schema(self):
        connection.cursor().execute('CREATE SCHEMA "%s";' %self.schema)
    
    def activate(self):
        connection.cursor().execute('SET search_path TO "%s",public' % self.schema)

class UserSchema(models.Model):
    user = models.OneToOneField(User, related_name='schema')
    schema = models.ForeignKey(Schema, related_name='users')
    
    class Meta:
        app_label = 'multi_schema'
    
    def __unicode__(self):
        return u"%s : %s" % (self.user, self.schema)


class SchemaAwareModel(models.Model):
    """
    The Base class for models that should be in a seperate schema.
    """
    _is_schema_aware = True

    class Meta:
        abstract = True
