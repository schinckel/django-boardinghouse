"""
"""
import logging

from django.conf import settings
from django.core.cache import cache
from django.core.validators import RegexValidator
from django.db import models
from django.forms import ValidationError
from django.utils import six
from django.utils.translation import ugettext_lazy as _

from .base import SharedSchemaMixin
from .schema import _schema_exists, activate_schema, deactivate_schema
from . import signals

LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.NullHandler())

SCHEMA_NAME_VALIDATOR_MESSAGE = u'May only contain lowercase letters, digits and underscores. '\
                                u'Must start with a letter.'

schema_name_validator = RegexValidator(
    regex=r'^[a-z][a-z0-9_]*$',
    message=_(SCHEMA_NAME_VALIDATOR_MESSAGE)
)


class SchemaQuerySet(models.query.QuerySet):
    def bulk_create(self, *args, **kwargs):
        # Normally a bulk_create would not trigger the post_save signal for
        # each instance. We need to rely on that firing to create the actual
        # database schema, so we manually trigger that signal.
        created = super(SchemaQuerySet, self).bulk_create(*args, **kwargs)
        for schema in created:
            models.signals.post_save.send(sender=self.model,
                                          instance=schema,
                                          created=True)
        cache.delete('active-schemata')
        return created

    def mass_create(self, *args):
        # A helper method that creates schemata with name/schema the same.
        # Perhaps it could slugify the schema value?
        self.bulk_create([self.model(name=x, schema=x) for x in args])
        cache.delete('active-schemata')
        # Need to be able to supply the schemata in the order they were passed in,
        # but a version that has been loaded from the database: otherwise the database
        # will not be set, and using these will fail.
        schemata = {x.schema: x for x in self.model.objects.filter(schema__in=args)}
        return [schemata[x] for x in args]

    def active(self):
        return self.filter(is_active=True)

    def inactive(self):
        return self.filter(is_active=False)

    def delete(self, drop=False, connection=None):
        if drop:
            schemata = list(self.values_list('schema', flat=True))
            super(SchemaQuerySet, self).delete()
            signals.schemata_deleted.send(sender=self.model, schemata=schemata, connection=connection)
        else:
            self.update(is_active=False)

    def activate(self, pk):
        self.get(pk=pk).activate()


@six.python_2_unicode_compatible
class AbstractSchema(SharedSchemaMixin, models.Model):
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

    objects = SchemaQuerySet.as_manager()

    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        super(AbstractSchema, self).__init__(*args, **kwargs)
        self._initial_schema = self.schema

    def __str__(self):
        return '{0} ({1})'.format(self.name, self.schema)

    def save(self, *args, **kwargs):
        self._meta.get_field('schema').run_validators(self.schema)

        # We want to prevent someone creating a new schema with
        # the same internal name as an existing one. We assume that
        # if we haven't been saved, then there should not be a
        # schema in the database with this name.
        if self._initial_schema in [None, ''] or 'force_insert' in kwargs:
            if _schema_exists(self.schema):
                raise ValidationError(_('Schema %s already in use') % self.schema)
        elif self.schema != self._initial_schema:
            raise ValidationError(_('may not change schema after creation.'))

        return super(AbstractSchema, self).save(*args, **kwargs)

    def delete(self, drop=False):
        if drop:
            super(AbstractSchema, self).delete()
        else:
            self.is_active = False
            self.save()

    def activate(self, cursor=None):
        activate_schema(self.schema)

    @classmethod
    def deactivate(cls, cursor=None):
        deactivate_schema()


class Schema(AbstractSchema):
    """
    The default schema model.

    Unless you set `settings.BOARDINGHOUSE_SCHEMA_MODEL`, this model will
    be used for storing the schema objects.
    """
    users = models.ManyToManyField(settings.AUTH_USER_MODEL,
        blank=True, related_name='schemata',
        help_text=_(u'Which users may access data from this schema.')
    )

    class Meta:
        app_label = 'boardinghouse'
        verbose_name_plural = 'schemata'
        swappable = 'BOARDINGHOUSE_SCHEMA_MODEL'


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


# Add a cached method that prevents user.schemata.all() queries from
# being needlessly duplicated.
def visible_schemata(user):
    """The list of visible schemata for the given user.

    This is fetched from the cache, if the value is available. There are
    signal listeners that automatically invalidate the cache when conditions
    that are detected that would indicate this value has changed.
    """
    schemata = cache.get('visible-schemata-{0!s}'.format(user.pk))
    if schemata is None:
        schemata = user.schemata.active()
        cache.set('visible-schemata-{0!s}'.format(user.pk), schemata)

    return schemata
