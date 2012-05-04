from django.conf import settings
from django.contrib.auth.models import User
from django.db import models, connection, transaction
from django.utils.translation import ugettext as _

class ClassProperty(property):
    def __get__(self, cls, owner):
        return self.fget.__get__(None, owner)()

def is_schema_aware(cls):
    return cls._meta.auto_created and cls._meta.auto_created._is_schema_aware
    
models.Model._is_schema_aware = ClassProperty(classmethod(is_schema_aware))

from multi_schema import signals

class Schema(models.Model):
    name = models.CharField(max_length=128, help_text=_(u'The display name of the schema.'))
    schema = models.CharField(max_length=36, unique=True, 
        help_text=_(u'The internal name of the schema. May not be changed after creation.'))
    
    class Meta:
        app_label = 'multi_schema'
    
    def __unicode__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.pk:
            self.create_schema()
        return super(Schema, self).save(*args, **kwargs)
    
    def create_schema(self, cursor=None):
        if not cursor:
            cursor = connection.cursor()
        cursor.execute("SELECT clone_schema('__template__', '%s');" % self.schema)
        transaction.commit_unless_managed()
        signals.schema_created.send(sender=self, schema=self.schema)
    
    def activate(self, cursor=None):
        signals.schema_pre_activate.send(sender=self, schema=self.schema)
        (cursor or connection.cursor()).execute('SET search_path TO "%s",public' % self.schema)
        signals.schema_post_activate.send(sender=self, schema=self.schema)        

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
