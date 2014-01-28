import inspect

from django.db.backends.postgresql_psycopg2 import schema

from ...schema import is_shared_model, get_schema_model, get_template_schema

def wrap(name):
    method = getattr(schema.DatabaseSchemaEditor, name)
    
    def _apply_to_all(self, model, *args, **kwargs):
        if is_shared_model(model):
            return method(self, model, *args, **kwargs)
        
        if '_apply_to_all' in [x[3] for x in inspect.stack()[1:]]:
            return method(self, model, *args, **kwargs)
        
        for schema in get_schema_model().objects.all():
            schema.activate()
            method(self, model, *args, **kwargs)
        
        get_template_schema().activate()
        method(self, model, *args, **kwargs)
        
        get_template_schema().deactivate()
    
    return _apply_to_all
    
class DatabaseSchemaEditor(schema.DatabaseSchemaEditor):
    column_sql = wrap('column_sql')
    create_model = wrap('create_model')
    delete_model = wrap('delete_model')
    alter_unique_together = wrap('alter_unique_together')
    alter_index_together = wrap('alter_index_together')
    alter_db_table = wrap('alter_db_table')
    add_field = wrap('add_field')
    remove_field = wrap('remove_field')
    alter_field = wrap('alter_field')
