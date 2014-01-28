import os

import django
from django.conf import settings
from django.db import models, connection

class Forbidden(Exception):
    pass

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
    return models.get_model(*settings.SCHEMA_MODEL.split('.'))

def get_template_schema():
    return get_schema_model()(schema="__template__")

def get_schema():
    """
    Get the currently active schema.
    
    This requires a database query to ask it what the current `search_path` is.
    """
    cursor = connection.cursor()
    cursor.execute('SHOW search_path')
    search_path = cursor.fetchone()[0]
    cursor.close()
    schema_name = search_path.split(',')[0]
    if schema_name == '__template__':
        return get_template_schema()
    
    Schema = get_schema_model()
    
    try:
        return Schema.objects.get(schema=schema_name)
    except Schema.DoesNotExist:
        return None

def activate_schema(schema):
    """
    Activate the schema provided, or with the name provided.
    
    This will raise a :class:`TemplateSchemaActivation` exception if
    the __template__ schema is attempted to be activated.
    """
    Schema = get_schema_model()
    
    if isinstance(schema, Schema):
        if schema.schema == '__template__':
            raise TemplateSchemaActivation()
        schema.activate()
    else:
        if schema == '__template__':
            raise TemplateSchemaActivation()
        Schema.objects.get(schema=schema).activate()

def deactivate_schema(schema=None):
    """
    Deactivate the provided (or current) schema.
    """
    get_template_schema().deactivate()

def _auto_or_fk_to_shared(field):
    if field.primary_key:
        return True
    if field.rel:
        return is_shared_model(field.rel.get_related_field().model)
    
def is_shared_model(model):
    """
    Is the model (or instance of a model) one that should be in the
    public/shared schema?
    """
    if model._is_shared_model:
        return True
    
    if django.VERSION < (1, 6):
        app_model = '%s.%s' % (
            model._meta.app_label,
            model._meta.object_name.lower()
        )
    else:
        app_model = '%s.%s' % (
            model._meta.app_label, 
            model._meta.model_name
        )
    
    if app_model in settings.SHARED_MODELS:
        return True
    
    # if all fields are either autofield or foreignkey, and all fk fields
    # point to shared models, then we must be a shored model.
    if all([
        _auto_or_fk_to_shared(field) for field in model._meta.fields
    ]):
        return True
    
    return False

def is_shared_table(table):
    """
    Is the model from the provided database table name shared?
    
    We may need to look and see if we can work out which models
    this table joins.
    """
    # Get a mapping of all table names to models.
    table_map = dict([
        (x._meta.db_table, x) for x in models.get_models()
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
        rel_model = model._meta.get_field_by_name(
            table.replace(db_table, '').lstrip('_')
        )[0].rel.get_related_field().model
    
    return is_shared_model(model) and is_shared_model(rel_model)
    
## Internal helper functions.
def _get_schema_or_template():
    """
    Get the name of the current schema, or __template__ if none is selected.
    
    This is really only intended to be used within code that deals with
    table creation or migration, as the __template__ schema should not be
    used at other times.
    """
    schema = get_schema()
    if not schema:
        return '__template__'
    return schema.schema

def _install_clone_schema_function():
    """
    A large part of this project is based around how simple it is to
    clone a schema's structure into a new schema. This is encapsulated in
    an SQL script: this function will install that function into the current
    database.
    """
    clone_schema_file = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'sql', 'clone_schema.sql')
    clone_schema_function = " ".join([x.strip() for x in open(clone_schema_file).readlines() if not x.strip().startswith('--')])
    clone_schema_function = clone_schema_function.replace("%", "%%")
    cursor = connection.cursor()
    cursor.execute(clone_schema_function)
    cursor.close()
