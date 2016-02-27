from __future__ import unicode_literals

from collections import defaultdict

from django.db.backends.postgresql_psycopg2 import schema

import sqlparse
from sqlparse.tokens import DDL, DML, Keyword

from ...schema import is_shared_table
from ...schema import get_schema_model, _schema_table_exists
from ...schema import deactivate_schema, activate_template_schema
from ...schema import _get_public_schema


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
    """, [_get_public_schema(), "__template__", table_name])
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
    """, [_get_public_schema(), "__template__", table_name])
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
    """, [_get_public_schema(), '__template__', table_name])
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

    cursor.execute('''SELECT c.relname AS table_name, n.nspname AS schema_name
                        FROM pg_catalog.pg_class c, pg_catalog.pg_class c2,
                             pg_catalog.pg_index idx, pg_catalog.pg_namespace n
                       WHERE c.oid = idx.indrelid
                         AND idx.indexrelid = c2.oid
                         AND n.oid = c.relnamespace
                         AND n.nspname IN (%s, %s)
                         AND c2.relname = %s
    ''', [_get_public_schema(), '__template__', index_name])

    return [table_name for (table_name, schema_name) in cursor.fetchall()]


def is_inherited_from(table_name, cursor):
    query = '''SELECT count(*) > 0
                 FROM pg_catalog.pg_inherits i
           INNER JOIN pg_catalog.pg_class c ON (i.inhrelid = c.oid)
           INNER JOIN pg_catalog.pg_namespace n ON (c.relnamespace = n.oid)
                WHERE c.relname = %s'''
    cursor.execute(query, [table_name])
    return cursor.fetchone()[0]


def query_data(sql, cursor):
    """
    Returns: (statement, table_name, schema_name)
    """
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
        if keywords[0] == 'INDEX' and grouped[DDL][0] == 'DROP':
            return 'DROP INDEX', get_index_data(cursor, identifiers[0].get_name())[0], None
        if keywords[0] in ['VIEW', 'TABLE']:
            # We care about identifier 0
            if identifiers:
                return '{} {}'.format(grouped[DDL][0], keywords[0]), identifiers[0].get_name(), identifiers[0].get_parent_name()
        elif keywords[0] in ['TRIGGER', 'INDEX']:
            # We care about identifier 1
            if len(identifiers) > 1:
                return '{} {}'.format(grouped[DDL][0], keywords[0]), identifiers[1].get_name(), identifiers[1].get_parent_name()

    # We also care about other non-DDL statements, as the implication is
    # that they should apply to every known schema, if we are updating as
    # part of a migration.
    if grouped[DML] and grouped[DML][0] in ['INSERT INTO', 'UPDATE', 'DELETE FROM']:
        if identifiers:
            return grouped[DML][0], identifiers[0].get_name(), identifiers[0].get_parent_name()

    return parsed.tokens[0], None, None


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
        self.deferred_sql = deferred_sql + getattr(self, '_extra_deferred_sql', [])
        # self.deferred_sql = deferred_sql
        return super(DatabaseSchemaEditor, self).__exit__(exc_type, exc_value, traceback)
        # If we manage to rewrite the SQL so it injects schema clauses, then we can remove this override.

    def execute(self, sql, params=None):
        # We want to execute our SQL multiple times, if it is per-schema.
        execute = super(DatabaseSchemaEditor, self).execute
        if 'CREATE TABLE i_love_ponies' in sql:
            import pdb; pdb.set_trace()

        statement, table_name, schema_name = query_data(sql, self.connection.cursor())

        def apply_to_template():
            activate_template_schema()
            execute(sql, params)
            deactivate_schema()

        def apply_to_all(operation, *args):
            if _schema_table_exists():
                for each in get_schema_model().objects.all():
                    each.activate()
                    operation(*args)
            deactivate_schema()

        # If there was an explicit schema_name, or no table_name, or our
        # table_name indicates this is a shared table, then we can just
        # jump down and execute the statement normally.
        if table_name and not schema_name and not is_shared_table(table_name):

            # Under certain circumstances, we don't ever need to operate on
            # all of the schemata. This would be if we are performing an
            # operation on a table, and the table is already inherited,
            # unless it's a UNIQUE, PK or FK constraint.
            # Unfortunately, it's not possible to distinguish between:
            # ALTER TABLE <x> DROP CONSTRAINT <y>
            # Where Y was a CHECK constraint, or a UNIQUE, or PK or FK.
            if (statement in ['DROP TABLE', 'ALTER TABLE'] and
                is_inherited_from(table_name, self.connection.cursor())
               ):
                if ('DROP CONSTRAINT' in sql or
                    'ALTER CONSTRAINT' in sql or
                    'RENAME CONSTRAINT' in sql
                   ):
                    constraints = get_constraints(self.connection.cursor(), table_name)
                    for name, definition in constraints.items():
                        if name in sql:
                            # This is the constraint we are dropping. If it is anything except a CHECK constraint, then we need to remove it from all tables.
                            if not definition['check']:
                                apply_to_all(execute, sql, params)
                            break
                elif (('ALTER COLUMN' in sql and 'DEFAULT' in sql) or
                      ('ADD CONSTRAINT' in sql and 'CHECK' not in sql)):
                    apply_to_all(execute, sql, params)
                else:
                    pass
                apply_to_template()
            elif _schema_table_exists():
                apply_to_template()
                self._extra_deferred_sql = []
                if statement == 'CREATE TABLE':
                    for each in get_schema_model().objects.all():
                        execute('CREATE TABLE "{0}"."{1}" (LIKE "__template__"."{1}" INCLUDING ALL)'.format(each.schema, table_name))
                        self._extra_deferred_sql.append(
                            'ALTER TABLE "{0}"."{1}" INHERIT "__template__"."{1}"'.format(each.schema, table_name)
                        )
                else:
                    apply_to_all(execute, sql, params)
            else:
                apply_to_template()
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
