"""
"""

import django
from django.conf import settings
from django.contrib import auth
from django.db import models, connection, transaction
from django.utils.translation import ugettext_lazy as _
from django.core.validators import RegexValidator
from django.forms import ValidationError

if django.VERSION < (1,7):
    from model_utils.managers import PassThroughManager
else:
    pass

import ensure_installation
import signals


class SchemaQuerySet(models.query.QuerySet):
    def bulk_create(self, *args, **kwargs):
        created = super(SchemaQuerySet, self).bulk_create(*args, **kwargs)
        for schema in created:
            schema.create_schema()
        return created
    
    def mass_create(self, *args):
        self.bulk_create([Schema(name=x, schema=x) for x in args])


schema_name_validator = RegexValidator(
    regex='^[a-z][a-z_]*$',
    message=_(u'May only contain lowercase letters and underscores. Must start with a letter.')
)


class AbstractBaseSchema(models.Model):
    """
    The Schema model provides an abstraction for a Postgres schema.
    
    It will take care of creating a cloned copy of the template_schema
    when it is created, and also has the ability to activate and deactivate
    itself (at the start and end of the request cycle would be a good plan).
    """
    _is_shared_model = True
    
    schema = models.CharField(max_length=36, primary_key=True, unique=True,
        validators=[schema_name_validator],
        help_text=_(u'The internal name of the schema. May not be changed after creation.'),
    )
    
    if django.VERSION < (1,7):
        objects = PassThroughManager.for_queryset_class(SchemaQuerySet)()
    else:
        objects = SchemaQuerySet.as_manager()
    
    class Meta:
        abstract = True
    
    def __init__(self, *args, **kwargs):
        super(AbstractBaseSchema, self).__init__(*args, **kwargs)
        self._initial_schema = self.schema

    def __unicode__(self):
        return self.schema
    
    def save(self, *args, **kwargs):
        self._meta.get_field_by_name('schema')[0].run_validators(self.schema)
        
        # We want to prevent someone creating a new schema with
        # the same internal name as an existing one. We assume if we
        # were 'initialised' then we were loaded from the database
        # with those values.
        if self._initial_schema is None or 'force_insert' in kwargs:
            try:
                self.__class__.objects.get(schema=self.schema)
            except self.__class__.DoesNotExist:
                pass
            else:
                raise ValidationError(_('Schema %s already in use') % self.schema)
        elif self.schema != self._initial_schema:
            raise ValidationError(_('may not change schema after creation.'))

        self.create_schema()
        
        return super(AbstractBaseSchema, self).save(*args, **kwargs)
        
    def create_schema(self, cursor=None):
        if not cursor:
            cursor = connection.cursor()
            self.create_schema(cursor)
            return cursor.close()
        cursor.execute("SELECT schema_name FROM information_schema.schemata WHERE schema_name = %s", [self.schema])
        if not cursor.fetchone():
            cursor.execute("SELECT clone_schema('__template__', %s);", [self.schema])
            transaction.commit_unless_managed()
            signals.schema_created.send(sender=self, schema=self.schema)
    
    def activate(self, cursor=None):
        if not cursor:
            cursor = connection.cursor()
            self.activate(cursor)
            return cursor.close()
        signals.schema_pre_activate.send(sender=self, schema=self.schema)
        cursor.execute('SET search_path TO "%s",public' % self.schema)
        signals.schema_post_activate.send(sender=self, schema=self.schema)
    
    def deactivate(self, cursor=None):
        if not cursor:
            cursor = connection.cursor()
            self.deactivate(cursor)
            return cursor.close()
        signals.schema_pre_activate.send(sender=self, schema=None)
        cursor.execute('SET search_path TO "$user",public')
        signals.schema_post_activate.send(sender=self, schema=None)


if settings.SCHEMA_MODEL.lower() == 'boardinghouse.schema':
    class Schema(AbstractBaseSchema):
        name = models.CharField(max_length=128, unique=True, help_text=_(u'The display name of the schema.'))
    
        # tracker = FieldTracker(fields=['schema'])
        
        class Meta:
            app_label = 'boardinghouse'
            verbose_name_plural = 'schemata'
    
        def __unicode__(self):
            return self.name
    

# This is a bit of fancy trickery to stick the property _is_shared_model
# on every model class, returning False, unless it has been explicitly
# set to True in the model definition (see base.py for examples).

class ClassProperty(property):
    def __get__(self, cls, owner):
        return self.fget.__get__(None, owner)()

def _is_shared_model(cls):
    return cls._meta.auto_created and cls._meta.auto_created._is_shared_model

models.Model._is_shared_model = ClassProperty(classmethod(_is_shared_model))

# We need to monkey-patch __eq__ on models.Model
__old_eq__ = models.Model.__eq__
    
def __eq__(self, other):
    from .schema import is_shared_model
    if is_shared_model(self):
        return __old_eq__(self, other)
    return __old_eq__(self, other) and self._schema == other._schema

models.Model.__eq__ = __eq__

def inject_schema_attribute(sender, instance, **kwargs):
    """
    A signal listener that injects the current schema on the object
    just after it is instantiated.
    
    You may use this in conjunction with :class:`MultiSchemaMixin`, it will
    respect any value that has already been set on the instance.
    """
    from .schema import is_shared_model, get_schema
    if is_shared_model(sender):
        return
    if not getattr(instance, '_schema', None):
        instance._schema = get_schema()

models.signals.post_init.connect(inject_schema_attribute)
