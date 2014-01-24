import inspect
import sys

from south.db import postgresql_psycopg2, generic

from django.db import models

def is_model_aware(table):
    """
    Look up in the django model list for the model with this
    table name, and find out if it has the _is_schema_aware
    attribute set.
    """
    data = [x for x in models.get_models() if x._meta.db_table == table]
    if data:
        return data[0]._is_schema_aware

def wrap(name):
    # This is the main guts of the changes we need to make.
    # It looks at the table name, and determines if we need
    # to perform the operation <number-of-schemata>+1 times.
    # If so, it activates each schema in turn, and performs
    # it's task.
    function = getattr(postgresql_psycopg2.DatabaseOperations, name)
    
    def apply_to_all(self, table, *args, **kwargs):
        # If this model is naive, then we only want to run the wrapped
        # function normally.
        if not is_model_aware(table):
            return function(self, table, *args, **kwargs)
        
        # If we are already in a schema loop, like when one wrapped method
        # calls another one, we don't want to loop again in the inside
        # method (that's the one we are in now).
        # inspect.stack() gives us the current stack, we ignore the current
        # frame, and then we look at the fourth item in each element.
        # If we come across apply_to_all, that means we can just execute
        # the original function call.
        if 'apply_to_all' in [x[3] for x in inspect.stack()[1:]]:
            return function(self, table, *args, **kwargs)
        
        # Need a late import to prevent circular importing error.
        from boardinghouse.models import Schema, template_schema
        
        for schema in Schema.objects.all():
            schema.activate()
            function(self, table, *args, **kwargs)
            schema.deactivate()
        
        template_schema.activate()
        function(self, table, *args, **kwargs)
        template_schema.deactivate()
        
    return apply_to_all


class DatabaseOperations(postgresql_psycopg2.DatabaseOperations):
    add_column = wrap('add_column')
    alter_column = wrap('alter_column')
    clear_table = wrap('clear_table')
    create_index = wrap('create_index')
    create_primary_key = wrap('create_primary_key')
    create_table = wrap('create_table')
    create_unique = wrap('create_unique')
    delete_column = wrap('delete_column')
    delete_foreign_key = wrap('delete_foreign_key')
    delete_index = wrap('delete_index')
    delete_primary_key = wrap('delete_primary_key')
    delete_table = wrap('delete_table')
    delete_unique = wrap('delete_unique')
    delete_column = wrap('delete_column')
    delete_index = wrap('delete_index')
    delete_primary_key = wrap('delete_primary_key')
    # Hmm. I'm not sure we want to wrap these two, but may as well try.
    execute = wrap('execute')
    execute_many = wrap('execute_many')
    rename_column = wrap('rename_column')
    rename_table = wrap('rename_table')
        
    # These deliberately skip our immediate parent.
    # I wish I had commented why.
    def _db_type_for_alter_column(self, field):
        return super(postgresql_psycopg2.DatabaseOperations, self)._db_type_for_alter_column(field)

    def _alter_add_column_mods(self, *args, **kwargs):
        return super(postgresql_psycopg2.DatabaseOperations, self)._alter_add_column_mods(*args ,**kwargs)
    
    # This gets called within an existing command, so we just want to make
    # it so it sets the search path correctly before and after running
    # each command. This may potentially slow things down, but it's also
    # the only way to ensure it is correct.
    def add_deferred_sql(self, sql):
        from boardinghouse.schema import _get_schema_or_template
        schema = _get_schema_or_template()
        sql = "SET search_path TO %s,public; %s; SET search_path TO public;" % (schema, sql)
        self.deferred_sql.append(sql)
    
    # South uses some caching of constraints per table, we just override
    # this method to turn off that caching. That makes checks hit the
    # database each time, but that is better than trying to invalidate the
    # cache each time we change schema (which happens a lot).
    def lookup_constraint(self, db_name, table_name, column_name=None):
        if is_model_aware(table_name):
            from boardinghouse.schema import _get_schema_or_template
            schema = _get_schema_or_template()
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
    