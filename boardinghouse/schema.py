import os

from django.db import models, connection

import settings
from .models import Schema, template_schema

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

def get_schema():
    """
    Get the currently active schema.
    
    This requires a database query to ask it what the current `search_path`
    is.
    """
    cursor = connection.cursor()
    cursor.execute('SHOW search_path')
    search_path = cursor.fetchone()[0]
    cursor.close()
    schema_name = search_path.split(',')[0]
    if schema_name == '__template__':
        return template_schema
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
    Schema().deactivate()

def is_shared_model(model):
    """
    Is the model (or instance of a model) one that should be in the
    public/shared schema?
    """
    if model._is_shared_model:
        return True
    
    app_model = '%s.%s' % (model._meta.app_label, model._meta.model_name)
    
    return app_model in settings.SHARED_MODELS

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