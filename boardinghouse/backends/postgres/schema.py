import inspect
import re

try:
    from django.db.backends.postgresql_psycopg2 import schema
except ImportError:
    pass
else:
    from ...schema import is_shared_model, is_shared_table
    from ...schema import get_schema_model
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

            for schema in get_schema_model().objects.all():
                schema.activate()
                method(self, model, *args, **kwargs)

            activate_template_schema()
            result = method(self, model, *args, **kwargs)
            deactivate_schema()
            return result

        return _apply_to_all

    CREATE_INDEX = re.compile(r'^CREATE INDEX\W+(?P<index_name>.+?) ON "(?P<table_name>.+?)" \("(?P<column_name>.+?)"\)$')
    ALTER_TABLE = re.compile(r'^ALTER TABLE\W+"?(?P<table_name>.+?)"? ADD (?P<type>(CONSTRAINT)|(CHECK)|(EXCLUDE))')
    CREATE_TRIGGER = re.compile(r'^\W*CREATE\W+TRIGGER\W+(?P<trigger_name>.+?)\W+.*?\W+ON\W+"?(?P<table_name>.+?)"?\W')
    DROP_TRIGGER = re.compile(r'^\W*DROP\W+TRIGGER\W+(?P<trigger_name>.+?)\W+ON\W+"?(?P<table_name>.+?)"?')
    CREATE_VIEW = re.compile(r'^CREATE( OR REPLACE)? VIEW\W+(?P<table_name>.+?) ')
    DROP_VIEW = re.compile(r'^DROP VIEW( IF EXISTS)?\W+(?P<table_name>[^;\W]+)')

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

        def __exit__(self, exc_type, exc_value, traceback):
            # It seems that actions that add stuff to the deferred sql
            # will fire per-schema, so we can end up with multiples.
            # We'll reduce that to a unique list.
            # Can't just do a set, as that may change ordering.
            deferred_sql = []
            for sql in self.deferred_sql:
                if sql not in deferred_sql:
                    deferred_sql.append(sql)
            self.deferred_sql = deferred_sql
            return super(DatabaseSchemaEditor, self).__exit__(exc_type, exc_value, traceback)

        def execute(self, sql, params=None):
            match = None
            if CREATE_INDEX.match(sql):
                match = CREATE_INDEX.match(sql).groupdict()
            elif ALTER_TABLE.match(sql):
                match = ALTER_TABLE.match(sql).groupdict()
            elif CREATE_TRIGGER.match(sql):
                match = CREATE_TRIGGER.match(sql).groupdict()
            elif DROP_TRIGGER.match(sql):
                match = DROP_TRIGGER.match(sql).groupdict()
            elif CREATE_VIEW.match(sql):
                match = CREATE_VIEW.match(sql).groupdict()
            elif DROP_VIEW.match(sql):
                match = DROP_VIEW.match(sql).groupdict()

            execute = super(DatabaseSchemaEditor, self).execute

            if match and not is_shared_table(match['table_name']):
                for schema in get_schema_model().objects.all():
                    schema.activate()
                    execute(sql, params)

                activate_template_schema()
                execute(sql, params)
                deactivate_schema()
            else:
                execute(sql, params)


