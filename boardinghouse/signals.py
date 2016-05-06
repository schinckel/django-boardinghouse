"""
Signals that are fired as part of the django-boardinghouse project.

.. data:: schema_created

    Sent when a new schema object has been created in the database. Accepts a
    single argument, the (internal) name of the schema.

.. data:: schema_pre_activate

    Sent just before a schema will be activated. May be used to abort this by
    throwing an exception.

.. data:: schema_post_activate

    Sent immediately after a schema has been activated.

.. data:: session_requesting_schema_change

    Sent when a user-session has requested (and is, according to default rules,
    allowed to change to this schema). May be used to prevent the change, by
    throwing an exception.

.. data:: session_schema_changed

    Sent when a user-session has changed it's schema.

.. data:: schema_aware_operation

    Sent when a migration operation that needs to be applied to each schema is
    due to be applied. Internally, this signal is used to ensure that the
    template schema and all currently existing schemata have the migration
    applied to them.

    This is also used by the ``contrib.template`` app to ensure that operations
    are applied to :class:`boardinghouse.contrib.template.models.SchemaTemplate`
    instances.

"""

import logging

from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.dispatch import Signal

from .schema import (
    _schema_exists, _schema_table_exists, activate_template_schema,
    get_active_schema_name, get_schema_model, is_shared_model,
)

LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.NullHandler())

# Provided signals.

schema_created = Signal(providing_args=["schema"])

schema_pre_activate = Signal(providing_args=["schema"])
schema_post_activate = Signal(providing_args=["schema"])

session_requesting_schema_change = Signal(providing_args=["user", "schema", "session"])
session_schema_changed = Signal(providing_args=["user", "schema", "session"])

schema_aware_operation = Signal(providing_args=['db_table', 'sql', 'params', 'execute'])


# Signal handlers.

def create_schema(sender, instance, created, **kwargs):
    """
    Actually create the schema in the database.

    We do this in a signal handler instead of .save() so we can catch
    those created using raw methods.

    How do we indicate when we should be using a different template?
    """
    if created:
        schema_name = instance.schema

        # How can we work out what values need to go here?
        # Currently, we just allow a single attribute `_clone`, that,
        # if set, will indicate that we should clone a schema.
        template_name = getattr(instance, '_clone', settings.TEMPLATE_SCHEMA)
        include_records = bool(getattr(instance, '_clone', False))

        cursor = connection.cursor()

        if _schema_exists(schema_name):
            raise ValueError('Attempt to create an existing schema: {}'.format(schema_name))

        cursor.execute("SELECT clone_schema(%s, %s, %s)", [
            template_name,
            schema_name,
            include_records
        ])
        cursor.close()

        if schema_name != settings.TEMPLATE_SCHEMA:
            schema_created.send(sender=get_schema_model(),
                                schema=schema_name)

        LOGGER.info('New schema created: %s', schema_name)


def drop_schema(sender, instance, **kwargs):
    cursor = connection.cursor()
    # Is there a way to do this without opening up an SQL injection hole?
    cursor.execute("DROP SCHEMA IF EXISTS {} CASCADE".format(instance.schema))
    LOGGER.info('Schema dropped: %s', instance.schema)


def inject_schema_attribute(sender, instance, **kwargs):
    """
    A signal listener that injects the current schema on the object
    just after it is instantiated.

    You may use this in conjunction with :class:`MultiSchemaMixin`, it will
    respect any value that has already been set on the instance.
    """
    if is_shared_model(sender):
        return
    if not getattr(instance, '_schema', None):
        instance._schema = get_active_schema_name()


def invalidate_cache(sender, **kwargs):
    """
    A signal listener designed to invalidate the cache of a single
    user's visible schemata items.
    """
    if kwargs['reverse']:
        cache.delete('visible-schemata-{instance.pk}'.format(**kwargs))
    else:
        if kwargs['pk_set']:
            for pk in kwargs['pk_set']:
                cache.delete('visible-schemata-{}'.format(pk))


def invalidate_all_user_caches(sender, **kwargs):
    """
    A signal listener that invalidates all schemata caches for all users
    who have access to the sender instance (schema).
    """
    cache.delete('active-schemata')
    for user in kwargs['instance'].users.values('pk'):
        cache.delete('visible-schemata-{pk}'.format(**user))


def invalidate_all_caches(sender, **kwargs):
    """
    Invalidate all schemata caches. Not entirely sure this one works.
    """
    if sender.name == 'boardinghouse':
        cache.delete('active-schemata')


def execute_on_all_schemata(sender, db_table, function, **kwargs):
    if _schema_table_exists():
        for each in get_schema_model().objects.all():
            each.activate()
            function(*kwargs.get('args', []), **kwargs.get('kwargs', {}))


def execute_on_template_schema(sender, db_table, function, **kwargs):
    activate_template_schema()
    function(*kwargs.get('args', []), **kwargs.get('kwargs', {}))
