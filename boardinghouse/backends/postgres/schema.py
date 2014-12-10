from __future__ import unicode_literals

import inspect
import re

from django.db.backends.postgresql_psycopg2 import schema

from ...schema import is_shared_model, is_shared_table
from ...schema import get_schema_model, _schema_table_exists
from ...schema import deactivate_schema, activate_template_schema


def wrap(name):
    method = getattr(schema.DatabaseSchemaEditor, name)

    def _apply_to_all(self, model, *args, **kwargs):
        if is_shared_model(model):
            result = method(self, model, *args, **kwargs)
            return result

        if '_apply_to_all' in [x[3] for x in inspect.stack()[1:]]:
            return method(self, model, *args, **kwargs)

        # Only do this if our table exists!
        if _schema_table_exists():
            for each in get_schema_model().objects.all():
                each.activate()
                method(self, model, *args, **kwargs)

        activate_template_schema()
        result = method(self, model, *args, **kwargs)
        deactivate_schema()
        return result

    return _apply_to_all

STATEMENTS = [
    re.compile(r'^\W*CREATE INDEX\W+(?P<index_name>.+?) ON "(?P<table_name>.+?)" \("(?P<column_name>.+?)"\)$'),
    re.compile(r'^\W*ALTER TABLE\W+"?(?P<table_name>.+?)"? ADD (?P<type>(CONSTRAINT)|(CHECK)|(EXCLUDE))'),
    re.compile(r'^\W*CREATE\W+TRIGGER\W+(?P<trigger_name>.+?)\W+.*?\W+ON\W+"?(?P<table_name>.+?)"?\W'),
    re.compile(r'^\W*DROP\W+TRIGGER\W+(?P<trigger_name>.+?)\W+ON\W+"?(?P<table_name>.+?)"?'),
    re.compile(r'^\W*CREATE( OR REPLACE)? VIEW\W+(?P<table_name>.+?) '),
    re.compile(r'^\W*DROP VIEW( IF EXISTS)?\W+(?P<table_name>[^;\W]+)'),
]


class DatabaseSchemaEditor(schema.DatabaseSchemaEditor):
    column_sql = wrap('column_sql')
    create_model = wrap('create_model')
    delete_model = wrap('delete_model')
    # alter_unique_together = wrap('alter_unique_together')
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
        for stmt in STATEMENTS:
            if stmt.match(sql):
                match = stmt.match(sql).groupdict()
                break

        execute = super(DatabaseSchemaEditor, self).execute

        if match and not is_shared_table(match['table_name']):
            if _schema_table_exists():
                for each in get_schema_model().objects.all():
                    each.activate()
                    execute(sql, params)

            activate_template_schema()
            execute(sql, params)
            deactivate_schema()
        else:
            execute(sql, params)
