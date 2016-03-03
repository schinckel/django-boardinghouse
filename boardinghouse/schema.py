import logging
import inspect
import threading

from django.apps import apps
from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.db.migrations.operations.base import Operation
from django.utils.translation import lazy

LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.NullHandler())

_thread_locals = threading.local()


class Forbidden(Exception):
    """
    An exception that will be raised when an attempt to activate a non-valid
    schema is made.
    """


class TemplateSchemaActivation(Forbidden):
    """
    An exception that will be raised when a user attempts to activate
    the __template__ schema.
    """
    def __init__(self, *args, **kwargs):
        super(TemplateSchemaActivation, self).__init__(
            'Activating template schema forbidden.', *args, **kwargs
        )


def get_schema_model():
    """
    Return the class that is currently set as the schema model.
    """
    return apps.get_model(settings.BOARDINGHOUSE_SCHEMA_MODEL)


def _get_search_path():
    cursor = connection.cursor()
    cursor.execute('SELECT current_schema()')
    search_path = cursor.fetchone()[0]
    cursor.close()
    return search_path.split(',')


def _set_search_path(search_path):
    cursor = connection.cursor()
    cursor.execute('SET search_path TO %s,{}'.format(settings.PUBLIC_SCHEMA),
                   [search_path])
    cursor.close()


def _schema_exists(schema_name, cursor=None):
    if cursor:
        cursor.execute('''SELECT schema_name
                            FROM information_schema.schemata
                           WHERE schema_name = %s''',
                       [schema_name])
        return bool(cursor.fetchone())

    cursor = connection.cursor()
    try:
        return _schema_exists(schema_name, cursor)
    finally:
        cursor.close()


def get_active_schema_name():
    """
    Get the currently active schema.

    This requires a database query to ask it what the current `search_path` is.
    """
    active_schema = getattr(_thread_locals, 'schema', None)

    if not active_schema:
        reported_schema = _get_search_path()[0]

        if _get_schema(reported_schema):
            active_schema = reported_schema
        else:
            active_schema = None

        _thread_locals.schema = active_schema

    return active_schema


def get_active_schema():
    """
    Get the (internal) name of the currently active schema.
    """
    return _get_schema(get_active_schema_name())


def get_active_schemata():
    """
    Get a (cached) list of all currently active schemata.
    """
    schemata = cache.get('active-schemata')
    if schemata is None:
        schemata = get_schema_model().objects.active()
        cache.set('active-schemata', schemata)
    return schemata


def get_all_schemata():
    """
    Get a (cached) list of all schemata.
    """
    schemata = cache.get('all-schemata')
    if schemata is None:
        schemata = get_schema_model().objects.all()
        cache.set('all-schemata', schemata)
    return schemata


def _get_schema(schema_name):
    """
    Get the matching active schema object for the given name,
    if it exists.
    """
    if not schema_name:
        return
    for schema in get_active_schemata():
        if schema_name == schema.schema or schema_name == schema:
            return schema


def activate_schema(schema_name):
    """
    Activate the current schema: this will execute, in the database
    connection, something like:

    .. code:: sql

        SET search_path TO "foo",public;

    It sends signals before and after that the schema will be, and was
    activated.

    Must be passed a string: the internal name of the schema to activate.
    """
    from .signals import schema_pre_activate, schema_post_activate

    if schema_name == '__template__':
        raise TemplateSchemaActivation()

    schema_pre_activate.send(sender=None, schema_name=schema_name)
    _set_search_path(schema_name)
    schema_post_activate.send(sender=None, schema_name=schema_name)
    _thread_locals.schema = schema_name


def activate_template_schema():
    """
    Activate the template schema.

    You probably don't want to do this. Sometimes you do (like for instance
    to apply migrations).
    """
    from .signals import schema_pre_activate, schema_post_activate

    _thread_locals.schema = None
    schema_name = '__template__'
    schema_pre_activate.send(sender=None, schema_name=schema_name)
    _set_search_path(schema_name)
    schema_post_activate.send(sender=None, schema_name=schema_name)


def get_template_schema():
    return get_schema_model()('__template__')


def deactivate_schema(schema=None):
    """
    Deactivate the provided (or current) schema.
    """
    from .signals import schema_pre_activate, schema_post_activate

    cursor = connection.cursor()
    schema_pre_activate.send(sender=None, schema_name=None)
    cursor.execute('SET search_path TO "$user",{}'.format(settings.PUBLIC_SCHEMA))
    schema_post_activate.send(sender=None, schema_name=None)
    _thread_locals.schema = None
    cursor.close()


#: These models are required to be shared by the system.
REQUIRED_SHARED_MODELS = [
    'auth.user',
    'auth.permission',
    'auth.group',
    'boardinghouse.schema',
    'sites.site',
    'sessions.session',
    'contenttypes.contenttype',
    'admin.logentry',
    'migrations.migration',
    # Maybe lazy() these? They only apply if the values for the settings.*
    # are not the defaults.
    lazy(lambda: settings.BOARDINGHOUSE_SCHEMA_MODEL.lower()),
    lazy(lambda: settings.AUTH_USER_MODEL.lower()),
]

REQUIRED_SHARED_TABLES = [
    'django_migrations',
]


def _is_join_model(model):
    """
    We define a model as a join model if all of it's
    fields are related fields (or it's primary key),
    and there is more than just one field.

    I am not 100% happy with this definition.
    """
    return all([
        (field.primary_key or field.rel)
        for field in model._meta.fields
    ]) and len(model._meta.fields) > 1


def is_shared_model(model):
    """
    Is the model (or instance of a model) one that should be in the
    public/shared schema?
    """
    if model._is_shared_model:
        return True

    app_model = '{m.app_label}.{m.model_name}'.format(m=model._meta).lower()

    # These should be case insensitive!
    if app_model in REQUIRED_SHARED_MODELS:
        return True

    if app_model in map(str.lower, settings.SHARED_MODELS):
        return True

    # Sometimes, we want a join table to be private.
    if app_model in map(str.lower, settings.PRIVATE_MODELS):
        return False

    # if all fields are auto or fk, then we are a join model,
    # and if all related objects are shared, then we must
    # also be shared, unless we were explicitly marked as private
    # above.
    if _is_join_model(model):
        return all([
            is_shared_model(field.rel.get_related_field().model)
            for field in model._meta.fields if field.rel
        ])

    return False


def is_shared_table(table, apps=apps):
    """
    Is the model from the provided database table name shared?

    We may need to look and see if we can work out which models
    this table joins.
    """
    if table in REQUIRED_SHARED_TABLES:
        return True

    # Get a mapping of all table names to models.
    models = apps.get_models()

    # If we are in a migration operation, we need to look in that for models.
    # We really only should be injecting ourselves if we find a frame that contains
    # a database_(forwards|backwards) function.
    for frame in inspect.stack():
        frame_locals = frame[0].f_locals
        if frame[3] == 'database_forwards' and all([
            local in frame_locals for local in ('from_state', 'to_state', 'schema_editor', 'self')
        ]) and isinstance(frame_locals['self'], Operation):
            # Should this be from_state, or to_state, or should we look in both?
            from_state = frame_locals['from_state']
            to_state = frame_locals['to_state']
            models = set()
            if to_state.apps:
                models = models.union(to_state.apps.get_models())
            if from_state.apps:
                models = models.union(from_state.apps.get_models())
            break

    table_map = dict([
        (x._meta.db_table, x) for x in models
        if not x._meta.proxy
    ])

    # If we have a match, see if that one is shared.
    if table in table_map:
        return is_shared_model(table_map[table])

    # It may be a join table.
    prefixes = [
        (db_table, model) for db_table, model in table_map.items()
        if table.startswith(db_table)
    ]

    if len(prefixes) == 1:
        db_table, model = prefixes[0]
        rel_model = model._meta.get_field(
            table.replace(db_table, '').lstrip('_')
        ).rel.get_related_field().model
    elif len(prefixes) == 0:
        # No matching models found.
        # Assume this is not a shared table...
        return False
    else:
        return is_shared_model(model)

    return is_shared_model(model) and is_shared_model(rel_model)


# Internal helper functions.

def _schema_table_exists():
    table_name = get_schema_model()._meta.db_table
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM information_schema.tables WHERE table_name = %s", [table_name])
    return bool(cursor.fetchone())
