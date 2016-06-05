import logging

from django.conf import settings
from django.core.cache import cache
from django.db import connection, models
from django.dispatch import receiver

from boardinghouse import signals
from boardinghouse.schema import (
    _schema_exists, _schema_table_exists, activate_template_schema,
    get_active_schema_name, get_schema_model, is_shared_model,
    TemplateSchemaActivation, Forbidden,
)

LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.NullHandler())

Schema = get_schema_model()


@receiver(models.signals.post_save, sender=Schema, weak=False, dispatch_uid='create-schema')
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
            signals.schema_created.send(sender=get_schema_model(), schema=schema_name)

        LOGGER.info('New schema created: %s', schema_name)


@receiver(models.signals.post_delete, sender=Schema, weak=False)
def drop_schema(sender, instance, **kwargs):
    signals.schemata_deleted.send(sender=sender, schemata=[instance.schema])


@receiver(signals.schemata_deleted, weak=False)
def drop_schemata(sender, schemata, connection=None, **kwargs):
    from django import db
    cursor = (connection or db.connection).cursor()
    # Is there a way to do this without opening up an SQL injection hole?
    # I guess we have to rely on the fact that schema.schema is always a valid name...?
    sql = ';'.join(['DROP SCHEMA IF EXISTS {} CASCADE'.format(schema) for schema in schemata])
    if sql:
        cursor.execute(sql)
        for schema in schemata:
            LOGGER.info('Schema dropped: %s', schema)


@receiver(models.signals.post_init, sender=None)
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


@receiver(signals.schema_aware_operation)
def execute_on_all_schemata(sender, db_table, function, **kwargs):
    if _schema_table_exists():
        for each in get_schema_model().objects.all():
            each.activate()
            function(*kwargs.get('args', []), **kwargs.get('kwargs', {}))


@receiver(signals.schema_aware_operation)
def execute_on_template_schema(sender, db_table, function, **kwargs):
    activate_template_schema()
    function(*kwargs.get('args', []), **kwargs.get('kwargs', {}))


@receiver(signals.session_requesting_schema_change)
def check_schema_for_user(sender, schema, user, session, **kwargs):
    if schema == settings.TEMPLATE_SCHEMA:
        raise TemplateSchemaActivation()

    if not schema.startswith('_'):
        try:
            if user.is_superuser:
                return Schema.objects.get(schema=schema)
            return user.visible_schemata.get(schema=schema)
        except Schema.DoesNotExist:
            raise Forbidden


# Cache-related stuff.
# This should only be set up to work if the provided visible_schemata property is in use.

if hasattr(Schema, 'users') and hasattr(Schema.users, 'through'):
    @receiver(models.signals.m2m_changed, sender=Schema.users.through)
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

    @receiver(models.signals.post_save, sender=Schema)
    def invalidate_all_user_caches(sender, **kwargs):
        """
        A signal listener that invalidates all schemata caches for all users
        who have access to the sender instance (schema).
        """
        cache.delete('active-schemata')
        for user in kwargs['instance'].users.values('pk'):
            cache.delete('visible-schemata-{pk}'.format(**user))


@receiver(models.signals.pre_migrate)
def invalidate_all_caches(sender, **kwargs):
    """
    Invalidate all schemata caches. Not entirely sure this one works.
    """
    if sender.name == 'boardinghouse':
        cache.delete('active-schemata')


@receiver(signals.session_schema_changed, weak=False)
def flush_user_perms_cache(sender, user, **kwargs):
    if hasattr(user, '_perm_cache'):
        del user._perm_cache
    if hasattr(user, '_user_perm_cache'):
        del user._user_perm_cache
    if hasattr(user, '_group_perm_cache'):
        del user._group_perm_cache
