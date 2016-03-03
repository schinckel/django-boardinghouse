from __future__ import unicode_literals

from collections import defaultdict

from django.db.backends.postgresql_psycopg2 import schema
from django.conf import settings

import sqlparse
from sqlparse.tokens import DDL, DML, Keyword

from ...schema import is_shared_table
from ...schema import get_schema_model, _schema_table_exists
from ...schema import deactivate_schema, activate_template_schema


def get_constraints(cursor, table_name):
    """
    Retrieves any constraints or keys (unique, pk, fk, check, index) across one or more columns.

    This is copied (almost) verbatim from django, but replaces the use of "public" with "public" + "__template__".

    We assume that this will find the relevant constraint, and rely on our operations keeping the others in sync.
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
            kc.table_schema IN (%s, %s) AND
            kc.table_name = %s
        ORDER BY kc.ordinal_position ASC
    """, [settings.PUBLIC_SCHEMA, "__template__", table_name])
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
            kc.table_schema IN (%s, %s) AND
            kc.table_name = %s
    """, [settings.PUBLIC_SCHEMA, "__template__", table_name])
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
            AND n.nspname IN (%s, %s)
            AND c.relname = %s
    """, [settings.PUBLIC_SCHEMA, '__template__', table_name])
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


def get_index_data(cursor, index_name):

    cursor.execute('''SELECT
    c.relname AS table_name,
    n.nspname AS schema_name
FROM pg_catalog.pg_class c, pg_catalog.pg_class c2,
    pg_catalog.pg_index idx, pg_catalog.pg_namespace n
WHERE c.oid = idx.indrelid
    AND idx.indexrelid = c2.oid
    AND n.oid = c.relnamespace
    AND n.nspname IN (%s, %s)
    AND c2.relname = %s
    ''', [settings.PUBLIC_SCHEMA, '__template__', index_name])

    return [table_name for (table_name, schema_name) in cursor.fetchall()]


def get_table_and_schema(sql, cursor):
    parsed = sqlparse.parse(sql)[0]
    grouped = defaultdict(list)
    identifiers = []

    for token in parsed.tokens:
        if token.ttype:
            grouped[token.ttype].append(token.value)
        elif token.get_name():
            identifiers.append(token)

    if grouped[DDL] and grouped[DDL][0] in ['CREATE', 'DROP', 'ALTER', 'CREATE OR REPLACE']:
        # We may care about this.
        keywords = grouped[Keyword]
        # DROP INDEX does not have a table associated with it.
        # We will have to hit the database to see what schema(ta) have an index with that name.
        if 'FUNCTION' in keywords:
            return None, None
        if 'INDEX' in keywords and grouped[DDL][0] == 'DROP':
            return get_index_data(cursor, identifiers[0].get_name())[0], None
        if 'VIEW' in keywords or 'TABLE' in keywords:
            # We care about identifier 0
            if identifiers:
                return identifiers[0].get_name(), identifiers[0].get_parent_name()
        elif 'TRIGGER' in keywords or 'INDEX' in keywords:
            # We care about identifier 1
            if len(identifiers) > 1:
                return identifiers[1].get_name(), identifiers[1].get_parent_name()

    # We also care about other non-DDL statements, as the implication is that they
    # should apply to every known schema, if we are updating as part of a migration.
    if grouped[DML] and grouped[DML][0] in ['INSERT INTO', 'UPDATE', 'DELETE FROM']:
        if identifiers:
            return identifiers[0].get_name(), identifiers[0].get_parent_name()

    return None, None


class DatabaseSchemaEditor(schema.DatabaseSchemaEditor):

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
        # If we manage to rewrite the SQL so it injects schema clauses, then we can remove this override.

    def execute(self, sql, params=None):
        # We want to execute our SQL multiple times, if it is per-schema.
        execute = super(DatabaseSchemaEditor, self).execute

        table_name, schema_name = get_table_and_schema(sql, self.connection.cursor())

        # TODO: try to get the apps from current project_state, not global apps.
        if table_name and not schema_name and not is_shared_table(table_name):
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
