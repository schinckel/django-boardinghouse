import inspect
import re

try:
    from django.db.backends.postgresql_psycopg2 import schema
except ImportError:
    pass
else:
    from ...schema import is_shared_model, is_shared_table
    from ...schema import get_active_schemata
    from ...schema import activate_schema, deactivate_schema
    from ...schema import activate_template_schema

    def wrap(name):
        method = getattr(schema.DatabaseSchemaEditor, name)
        
        def _apply_to_all(self, model, *args, **kwargs):
            if is_shared_model(model):
                result = method(self, model, *args, **kwargs)
                return result
            
            if '_apply_to_all' in [x[3] for x in inspect.stack()[1:]]:
                return method(self, model, *args, **kwargs)
            
            for schema in get_active_schemata():
                schema.activate()
                method(self, model, *args, **kwargs)
            
            activate_template_schema()
            result = method(self, model, *args, **kwargs)
            deactivate_schema()
            return result
    
        return _apply_to_all
    
    CREATE_INDEX = re.compile(r'^CREATE INDEX (?P<index_name>.+?) ON "(?P<table_name>.+?)" \("(?P<column_name>.+?)"\)$')
    ADD_CONSTRAINT = re.compile(r'^ALTER TABLE "(?P<table_name>.+?)" ADD CONSTRAINT')
    
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
        
        def execute(self, sql, params=None):
            match = None
            if CREATE_INDEX.match(sql):
                match = CREATE_INDEX.match(sql).groupdict()
            elif ADD_CONSTRAINT.match(sql):
                match = ADD_CONSTRAINT.match(sql).groupdict()
            
            execute = super(DatabaseSchemaEditor, self).execute
            if match and not is_shared_table(match['table_name']):
                for schema in get_active_schemata():
                    schema.activate()
                    execute(sql, params)
                
                activate_template_schema()
                execute(sql, params)
                deactivate_schema()
            else:
                execute(sql, params)
                    
                
                