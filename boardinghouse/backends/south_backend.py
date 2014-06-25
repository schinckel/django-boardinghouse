import inspect
import sys

from django.db import models

from ..schema import (
    is_shared_table, get_active_schema_name,
    activate_template_schema,
    activate_schema, deactivate_schema,
    get_active_schemata,
)

try:
    from south.db import postgresql_psycopg2, generic
except ImportError:
    # We only need to do anything if south is installed.
    pass
else:

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
            if is_shared_table(table):
                return function(self, table, *args, **kwargs)

            # If we are already in a schema loop, like when one wrapped method
            # calls another one, we don't want to loop again in the inside
            # method (that's the one we are in now).
            # inspect.stack() gives us the current stack, we ignore the current
            # frame, and then we look at the fourth item in each element.
            # If we come across apply_to_all, that means we can just execute
            # the original function call.
            for frame in inspect.stack()[1:]:
                if frame[3] == 'apply_to_all':
                    return function(self, table, *args, **kwargs)

            for schema in get_active_schemata():
                schema.activate()
                function(self, table, *args, **kwargs)
                deactivate_schema()

            activate_template_schema()
            function(self, table, *args, **kwargs)
            deactivate_schema()

        return apply_to_all


    class DatabaseOperations(postgresql_psycopg2.DatabaseOperations):
        """
        We need to wrap all of the calls to our methods in a wrapper that
        will call the method [NUM_SCHEMAS+1] times (including the special
        __template__ schema).

        However, if the method is being called by another sibling method,
        then we don't want to have the duplicate calls.

        """
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
        # We can't wrap these, as we don't know if they should apply
        # to every schema or not!
        # execute = wrap('execute')
        # execute_many = wrap('execute_many')
        rename_column = wrap('rename_column')
        rename_table = wrap('rename_table')

        # This gets called within an existing command, so we just want to make
        # it so it sets the search path correctly before and after running
        # each command. This may potentially slow things down, but it's also
        # the only way to ensure it is correct.
        def add_deferred_sql(self, sql):
            schema = get_active_schema_name() or '__template__'
            sql = "SET search_path TO %s,public; %s; SET search_path TO public;" % (schema, sql)
            self.deferred_sql.append(sql)

        # South uses some caching of constraints per table, we just override
        # this method to turn off that caching. That makes checks hit the
        # database each time, but that is better than trying to invalidate the
        # cache each time we change schema (which happens a lot).
        def lookup_constraint(self, db_name, table_name, column_name=None):
            if is_shared_table(table_name):
                schema = self._get_schema_name()
            else:
                schema = get_active_schema_name() or '__template__'

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
