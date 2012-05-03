from django.conf import settings
from django.contrib.auth.models import User
from django.db import models, connection, transaction
from django.utils.translation import ugettext as _

models.Model._is_schema_aware = False

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
    
    def create_schema(self):
        cursor = connection.cursor()
        cursor.execute("SELECT clone_schema('__template__', %s);" % self.schema)
        transaction.commit_unless_managed()
        signals.schema_created.send(sender=self, schema=self.schema)
    
    def activate(self):
        signals.schema_pre_activate.send(sender=self, schema=self.schema)
        connection.cursor().execute('SET search_path TO "%s",public' % self.schema)
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
