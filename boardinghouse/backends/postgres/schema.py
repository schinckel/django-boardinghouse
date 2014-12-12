from __future__ import unicode_literals

import inspect
import re

from django.db.backends.postgresql_psycopg2 import schema

from ...schema import is_shared_model, is_shared_table
from ...schema import get_schema_model, _schema_table_exists
from ...schema import deactivate_schema, activate_template_schema


def in_apply_to_all():
    return '_apply_to_all' in [x[3] for x in inspect.stack()[2:]]


def wrap(name):
    method = getattr(schema.DatabaseSchemaEditor, name)

    def _apply_to_all(self, model, *args, **kwargs):
        if is_shared_model(model):
            result = method(self, model, *args, **kwargs)
            return result

        if in_apply_to_all():
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


def get_constraints(cursor, table_name):
    """
    Retrieves any constraints or keys (unique, pk, fk, check, index) across one or more columns.
    """
    constraints = {}
    # Loop over the key table, collecting things as constraints
    # This will get PKs, FKs, and uniques, but not CHECK
    cursor.execute("""
        SELECT
            kc.constraint_name,
            kc.column_name,
            c.constraint_type,
            array(SELECT table_name::text || '.' || column_name::text
                  FROM information_schema.constraint_column_usage
                  WHERE constraint_name = kc.constraint_name)
        FROM information_schema.key_column_usage AS kc
        JOIN information_schema.table_constraints AS c ON
            kc.table_schema = c.table_schema AND
            kc.table_name = c.table_name AND
            kc.constraint_name = c.constraint_name
        WHERE
            kc.table_schema = current_schema() AND
            kc.table_name = %s
        ORDER BY kc.ordinal_position ASC
    """, [table_name])
    for constraint, column, kind, used_cols in cursor.fetchall():
        # If we're the first column, make the record
        if constraint not in constraints:
            constraints[constraint] = {
                "columns": [],
                "primary_key": kind.lower() == "primary key",
                "unique": kind.lower() in ["primary key", "unique"],
                "foreign_key": tuple(used_cols[0].split(".", 1)) if kind.lower() == "foreign key" else None,
                "check": False,
                "index": False,
            }
        # Record the details
        constraints[constraint]['columns'].append(column)
    # Now get CHECK constraint columns
    cursor.execute("""
        SELECT kc.constraint_name, kc.column_name
        FROM information_schema.constraint_column_usage AS kc
        JOIN information_schema.table_constraints AS c ON
            kc.table_schema = c.table_schema AND
            kc.table_name = c.table_name AND
            kc.constraint_name = c.constraint_name
        WHERE
            c.constraint_type = 'CHECK' AND
            kc.table_schema = current_schema() AND
            kc.table_name = %s
    """, [table_name])
    for constraint, column in cursor.fetchall():
        # If we're the first column, make the record
        if constraint not in constraints:
            constraints[constraint] = {
                "columns": [],
                "primary_key": False,
                "unique": False,
                "foreign_key": None,
                "check": True,
                "index": False,
            }
        # Record the details
        constraints[constraint]['columns'].append(column)
    # Now get indexes
    cursor.execute("""
        SELECT
            c2.relname,
            ARRAY(
                SELECT (SELECT attname FROM pg_catalog.pg_attribute WHERE attnum = i AND attrelid = c.oid)
                FROM unnest(idx.indkey) i
            ),
            idx.indisunique,
            idx.indisprimary
        FROM pg_catalog.pg_class c, pg_catalog.pg_class c2,
            pg_catalog.pg_index idx, pg_catalog.pg_namespace n
        WHERE c.oid = idx.indrelid
            AND idx.indexrelid = c2.oid
            AND n.oid = c.relnamespace
            AND n.nspname = current_schema()
            AND c.relname = %s
    """, [table_name])
    for index, columns, unique, primary in cursor.fetchall():
        if index not in constraints:
            constraints[index] = {
                "columns": list(columns),
                "primary_key": primary,
                "unique": unique,
                "foreign_key": None,
                "check": False,
                "index": True,
            }
    return constraints

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
        for stmt in STATEMENTS:
            if stmt.match(sql):
                match = stmt.match(sql).groupdict()
                break

        execute = super(DatabaseSchemaEditor, self).execute

        if match and not is_shared_table(match['table_name']) and not in_apply_to_all():
            if _schema_table_exists():
                for each in get_schema_model().objects.all():
                    each.activate()
                    execute(sql, params)

            activate_template_schema()
            execute(sql, params)
            deactivate_schema()
        else:
            execute(sql, params)

    def _constraint_names(self, model, column_names=None, unique=None,
                          primary_key=None, index=None, foreign_key=None,
                          check=None):
        """
        Returns all constraint names matching the columns and conditions
        """
        column_names = list(column_names) if column_names else None
        with self.connection.cursor() as cursor:
            constraints = get_constraints(cursor, model._meta.db_table)
        result = []
        for name, infodict in constraints.items():
            if column_names is None or column_names == infodict['columns']:
                if unique is not None and infodict['unique'] != unique:
                    continue
                if primary_key is not None and infodict['primary_key'] != primary_key:
                    continue
                if index is not None and infodict['index'] != index:
                    continue
                if check is not None and infodict['check'] != check:
                    continue
                if foreign_key is not None and not infodict['foreign_key']:
                    continue
                result.append(name)

        return result