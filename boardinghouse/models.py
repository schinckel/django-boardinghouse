"""
"""
import logging

import django
from django.apps import apps
from django.conf import settings
from django.contrib import auth
from django.core.cache import cache
from django.core.validators import RegexValidator
from django.db import models, connection, transaction
from django.dispatch import receiver
from django.forms import ValidationError
from django.utils.translation import ugettext_lazy as _

import ensure_installation
import signals

from .base import SharedSchemaMixin
from .schema import (
    create_schema, activate_schema, deactivate_schema, get_active_schema_name,
)

LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.NullHandler())

SCHEMA_NAME_VALIDATOR_MESSAGE = u'May only contain lowercase letters, digits and underscores. Must start with a letter.'

schema_name_validator = RegexValidator(
    regex='^[a-z][a-z0-9_]*$',
    message=_(SCHEMA_NAME_VALIDATOR_MESSAGE)
)

class SchemaQuerySet(models.query.QuerySet):
    def bulk_create(self, *args, **kwargs):
        created = super(SchemaQuerySet, self).bulk_create(*args, **kwargs)
        for schema in created:
            schema.create_schema()
        cache.delete('active-schemata')
        return created

    def mass_create(self, *args):
        self.bulk_create([Schema(name=x, schema=x) for x in args])
        cache.delete('active-schemata')

    def active(self):
        return self.filter(is_active=True)

    def inactive(self):
        return self.filter(is_active=False)



class Schema(SharedSchemaMixin, models.Model):
    """
    The Schema model provides an abstraction for a Postgres schema.

    It will take care of creating a cloned copy of the template_schema
    when it is created, and also has the ability to activate and deactivate
    itself (at the start and end of the request cycle would be a good plan).
    """

    schema = models.CharField(max_length=36, primary_key=True, unique=True,
        validators=[schema_name_validator],
        help_text='<br>'.join([
            u'The internal name of the schema.',
            SCHEMA_NAME_VALIDATOR_MESSAGE,
            u'May not be changed after creation.',
        ]),
    )
    name = models.CharField(max_length=128, unique=True,
        help_text=_(u'The display name of the schema.')
    )
    is_active = models.BooleanField(default=True,
        help_text=_(u'Use this instead of deleting schemata.')
    )
    users = models.ManyToManyField(settings.AUTH_USER_MODEL,
        null=True, blank=True, related_name='schemata',
        help_text=_(u'Which users may access data from this schema.')
    )

    objects = SchemaQuerySet.as_manager()

    class Meta:
        app_label = 'boardinghouse'
        verbose_name_plural = 'schemata'

    def __init__(self, *args, **kwargs):
        super(Schema, self).__init__(*args, **kwargs)
        self._initial_schema = self.schema

    def __unicode__(self):
        return u'%s (%s)' % (self.name, self.schema)

    def save(self, *args, **kwargs):
        self._meta.get_field_by_name('schema')[0].run_validators(self.schema)

        # We want to prevent someone creating a new schema with
        # the same internal name as an existing one. We assume if we
        # were 'initialised' then we were loaded from the database
        # with those values.
        if self._initial_schema in [None, ''] or 'force_insert' in kwargs:
            try:
                self.__class__.objects.get(schema=self.schema)
            except self.__class__.DoesNotExist:
                pass
            else:
                raise ValidationError(_('Schema %s already in use') % self.schema)
        elif self.schema != self._initial_schema:
            raise ValidationError(_('may not change schema after creation.'))

        self.create_schema()

        return super(Schema, self).save(*args, **kwargs)

    def create_schema(self, cursor=None):
        """
        This method will create a new postgres schema with the name
        stored in 'self.schema', if it doesn't already exist in the
        database.

        At this stage, we just exit without failure (although log a warning)
        if the schema was already found in the database.
        """
        create_schema(self.schema)

    def activate(self, cursor=None):
        activate_schema(self.schema)

    @classmethod
    def deactivate(cls, cursor=None):
        deactivate_schema()


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
    from .schema import is_shared_model, get_active_schema_name
    if is_shared_model(sender):
        return
    if not getattr(instance, '_schema', None):
        instance._schema = get_active_schema_name()

models.signals.post_init.connect(inject_schema_attribute)

if 'django.contrib.admin' in settings.INSTALLED_APPS:
    # Patch LogEntry to store reference to Schema if applicable.
    from django.contrib.admin.models import LogEntry

    from .schema import is_shared_model

    if not getattr(LogEntry, 'object_schema', None):
        LogEntry.add_to_class(
            'object_schema',
            models.ForeignKey('boardinghouse.schema', blank=True, null=True)
        )

        # Now, when we have an object that gets saved in the admin, we
        # want to store the schema in the log, ...
        @receiver(models.signals.pre_save, sender=LogEntry)
        def update_object_schema(sender, instance, **kwargs):
            obj = instance.get_edited_object()

            if not is_shared_model(obj):
                # I think we may have an attribute schema on the object?
                instance.object_schema_id = obj._schema

        # ...so we can add that bit to the url, and have links in the admin
        # that will automatically change the schema for us.
        get_admin_url = LogEntry.get_admin_url

        def new_get_admin_url(self):
            if self.object_schema_id:
                return get_admin_url(self) + '?__schema=%s' % self.object_schema_id

            return get_admin_url(self)

        LogEntry.get_admin_url = new_get_admin_url

if 'django.contrib.auth' in settings.INSTALLED_APPS:
    from django.contrib.auth.models import AnonymousUser
    AnonymousUser.schemata = Schema.objects.none()
    AnonymousUser.visible_schemata = Schema.objects.none()

# Add a cached method that prevents user.schemata.all() queries from
# being needlessly duplicated.
def visible_schemata(user):
    schemata = cache.get('visible-schemata-%s' % user.pk)
    if schemata is None:
        schemata = user.schemata.active()
        cache.set('visible-schemata-%s' % user.pk, schemata)

    return schemata


# We also need to watch for changes to the user_schemata table, to invalidate
# this cache.
@receiver(models.signals.m2m_changed, sender=Schema.users.through)
def invalidate_cache(sender, **kwargs):
    if kwargs['reverse']:
        cache.delete('visible-schemata-%s' % kwargs['instance'].pk)
    else:
        if kwargs['pk_set']:
            for pk in kwargs['pk_set']:
                cache.delete('visible-schemata-%s' % pk)

# In addition, we need to clear out the schemata cache for all users
# related to a schema if that schema is changed - specifically, if it's
# active status is changed. However, we can't track this with
# django-model-utils, due to a bug in django.
# We will also clear out the global active schemata cache.
@receiver(models.signals.post_save, sender=Schema)
@receiver(signals.schema_created, sender=Schema)
def invalidate_all_user_caches(sender, **kwargs):
    cache.delete('active-schemata')
    cache.delete('all-schemata')
    for user in kwargs['instance'].users.values('pk'):
        cache.delete('visible-schemata-%s' % user['pk'])

# We also want to clear out all caches when we get a syncdb or migrate
# signal on our own app.
# How can we clear out all user caches? It depends upon
# the cache backend, right?
@receiver(models.signals.pre_migrate)
def invalidate_all_caches(sender, **kwargs):
    if sender.name == 'boardinghouse':
        cache.delete('active-schemata')
        cache.delete('all-schemata')
