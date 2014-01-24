import inspect
import sys

from south.db import postgresql_psycopg2, generic

from django.db import models

def is_model_aware(table):
    data = [x for x in models.get_models() if x._meta.db_table == table]
    if data:
        return data[0]._is_schema_aware

def wrap(name):
    function = getattr(postgresql_psycopg2.DatabaseOperations, name)
    
    def apply_to_all(self, table, *args, **kwargs):
        # Need a late import to prevent circular importing error.
        from boardinghouse.models import Schema, template_schema
        
        if not is_model_aware(table):
            return function(self, table, *args, **kwargs)
        
        for schema in Schema.objects.all():
            schema.activate()
            function(self, table, *args, **kwargs)
            schema.deactivate()
        
        template_schema.activate()
        function(self, table, *args, **kwargs)
        template_schema.deactivate()
        
    return apply_to_all
    
class DatabaseOperations(postgresql_psycopg2.DatabaseOperations):
    create_table = wrap('create_table')
    rename_table = wrap('rename_table')
    delete_table = wrap('delete_table')
    clear_table = wrap('clear_table')
    add_column = wrap('add_column')
    create_unique = wrap('create_unique')
    delete_unique = wrap('delete_unique')
    # delete_foreign_key = wrap('delete_foreign_key')
    create_index = wrap('create_index')
    delete_index = wrap('delete_index')
    drop_index = wrap('delete_index')
    delete_column = wrap('delete_column')
    drop_column = wrap('delete_column')
    rename_column = wrap('rename_column')
    delete_primary_key = wrap('delete_primary_key')
    drop_primary_key = wrap('delete_primary_key')
    create_primary_key = wrap('create_primary_key')
    
    # # Need custom handling, as this may be called by add_column.
    def alter_column(self, table_name, *args, **kwargs):
        operation = super(DatabaseOperations, self).alter_column
        # This is a bit hacky. We look in the call stack for the function that called us, and if that was add_column, then we just run the operation normally, as the wrapping is already in-place in the add_column call. If it is _anything_ else, then we need to wrap it to ensure it runs for every schema.
        stack = inspect.stack()
        if stack[1][3] != "add_column":
            operation = wrap('alter_column')
            return operation(self, table_name, *args, **kwargs)
        return operation(table_name, *args, **kwargs)

    # These deliberately skip our immediate parent.
    def _db_type_for_alter_column(self, field):
        return super(postgresql_psycopg2.DatabaseOperations, self)._db_type_for_alter_column(field)

    def _alter_add_column_mods(self, *args, **kwargs):
        return super(postgresql_psycopg2.DatabaseOperations, self)._alter_add_column_mods(*args ,**kwargs)
        
    def add_deferred_sql(self, sql):
        from boardinghouse.schema import get_schema_or_template
        schema = get_schema_or_template()
        sql = "SET search_path TO %s,public; %s; SET search_path TO public;" % (schema, sql)
        self.deferred_sql.append(sql)
    
    def lookup_constraint(self, db_name, table_name, column_name=None):
        if is_model_aware(table_name):
            from boardinghouse.schema import get_schema_or_template
            schema = get_schema_or_template()
        else:
            schema = self._get_schema_name()
        
        constraints = {}
        ifsc_tables = ["constraint_column_usage", "key_column_usage"]

        for ifsc_table in ifsc_tables:
            rows = self.execute("""
                SELECT kc.constraint_name, kc.column_name, c.constraint_type
                FROM information_schema.%s AS kc
                JOIN information_schema.table_constraints AS c ON
                    kc.table_schema = c.table_schema AND
                    kc.table_name = c.table_name AND
                    kc.constraint_name = c.constraint_name
                WHERE
                    kc.table_schema = %%s AND
                    kc.table_name = %%s
            """ % ifsc_table, [schema, table_name])
            
            for constraint, column, kind in rows:
                constraints.setdefault(column, set())
                constraints[column].add((kind, constraint))
        
        if column_name:
            return constraints.get(column_name, set())
        
        return constraints.items()
    