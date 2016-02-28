"""
Signals that are fired as part of the django-boardinghouse project.

.. data:: schema_created

.. data:: schema_pre_activate

.. data:: schema_post_activate

"""

import logging

from django.dispatch import Signal
from django.db import connection
from django.core.cache import cache

from .schema import (
    _schema_exists, is_shared_model, get_schema_model,
    get_active_schema_name
)

LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.NullHandler())

# Provided signals.

schema_created = Signal(providing_args=["schema"])

schema_pre_activate = Signal(providing_args=["schema"])
schema_post_activate = Signal(providing_args=["schema"])

session_requesting_schema_change = Signal(providing_args=["user", "schema", "session"])
session_schema_changed = Signal(providing_args=["user", "schema", "session"])


# Signal handlers.

def create_schema(sender, instance, created, **kwargs):
    """
    Actually create the schema in the database.

    We do this in a signal handler instead of .save() so we can catch
    those created using raw methods.
    """
    if created:
        schema_name = instance.schema

        cursor = connection.cursor()

        if _schema_exists(schema_name):
            LOGGER.warn('Attempt to create an existing schema: %s' % schema_name)
            return

        cursor.execute("SELECT clone_schema('__template__', %s)", [schema_name])
        cursor.close()

        if schema_name != '__template__':
            schema_created.send(sender=get_schema_model(), schema=schema_name)

        LOGGER.info('New schema created: %s' % schema_name)


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
    "Clear out the caches on changes to the user_schemata table."
    if kwargs['reverse']:
        cache.delete('visible-schemata-%s' % kwargs['instance'].pk)
    else:
        if kwargs['pk_set']:
            for pk in kwargs['pk_set']:
                cache.delete('visible-schemata-%s' % pk)


def invalidate_all_user_caches(sender, **kwargs):
    cache.delete('active-schemata')
    cache.delete('all-schemata')
    for user in kwargs['instance'].users.values('pk'):
        cache.delete('visible-schemata-%s' % user['pk'])


def invalidate_all_caches(sender, **kwargs):
    if sender.name == 'boardinghouse':
        cache.delete('active-schemata')
        cache.delete('all-schemata')
