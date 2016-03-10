from __future__ import unicode_literals

from collections import defaultdict

from django.db.backends.postgresql_psycopg2 import schema
from django.conf import settings

import sqlparse
from sqlparse.tokens import DDL, DML, Keyword

from ...schema import deactivate_schema, is_shared_table
from ...signals import schema_aware_operation


def get_constraints(cursor, table_name, schema_name='__template__'):
    """Return all constraints for a given table

    (in either the given schema, or the public schema: the assumption is made
    that constraint names will not be the same in both).

    """
    cursor.execute("""
WITH constraints AS (

          SELECT tc.constraint_type,
                 tc.constraint_name,
                 COALESCE(ccu.column_name, kcu.column_name) AS column_name
            FROM information_schema.table_constraints AS tc
 LEFT OUTER JOIN information_schema.constraint_column_usage AS ccu
           USING (table_schema, table_name, constraint_name)
 LEFT OUTER JOIN information_schema.key_column_usage AS kcu
           USING (table_schema, table_name, constraint_name)
           WHERE tc.table_schema IN (%s, %s)
             AND tc.table_name = %s

             UNION

          SELECT 'INDEX' AS constraint_type,
                 id.indexname AS constraint_name,
                 attr.attname AS column_name
            FROM pg_catalog.pg_indexes AS id
      INNER JOIN pg_catalog.pg_index  AS idx
              ON (id.schemaname || '.' || id.indexname)::regclass = idx.indexrelid
 LEFT OUTER JOIN pg_catalog.pg_attribute AS attr
              ON idx.indrelid = attr.attrelid AND attr.attnum = ANY(idx.indkey)
           WHERE id.schemaname IN (%s, %s)
             AND id.tablename = %s
),
by_type AS (
  SELECT constraint_type,
         constraint_name,
         array_agg(column_name ORDER BY column_name) AS columns
    FROM constraints
   WHERE column_name IS NOT NULL
GROUP BY constraint_name, constraint_type
),
by_name AS (
  SELECT array_agg(constraint_type) AS constraints,
         constraint_name,
         columns
    FROM by_type
GROUP BY constraint_name, columns
)


SELECT constraint_name,
       columns,
       'PRIMARY KEY' = ANY(constraints) AS "primary_key",
       'UNIQUE' = ANY(constraints) OR 'PRIMARY KEY' = ANY(constraints) AS "unique",
       CASE WHEN 'FOREIGN KEY' = ANY(constraints) THEN
           (SELECT ARRAY[table_name::text, column_name::text]
                    FROM information_schema.constraint_column_usage ccu
                   WHERE by_name.constraint_name = ccu.constraint_name
                   LIMIT 1)
       END AS "foreign_key",
       'CHECK' = ANY(constraints) AS "check",
       'INDEX' = ANY(constraints) AS "index"
FROM by_name""", [settings.PUBLIC_SCHEMA, schema_name, table_name] * 2)
    columns = [x.name for x in cursor.description]
    return {row[0]: dict(zip(columns, row)) for row in cursor}


def get_index_data(cursor, index_name):

    cursor.execute('''SELECT c.relname AS table_name,
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
    try:
        parsed = sqlparse.parse(sql)[0]
    except IndexError:
        # In the case of a CREATE * FUNCTION that is a plpgsql function, we
        # know we won't be able to parse it. Functions should probably be in
        # the public schema anyway.
        sql_upper = sql.upper()
        if (
            'CREATE FUNCTION' in sql_upper or
            'CREATE OR REPLACE FUNCTION' in sql_upper
        ) and 'LANGUAGE PLPGSQL' in sql_upper:
            return None, None
        raise

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
        if 'FUNCTION' in keywords:
            # At this point, I'm not convinced that functions belong anywhere
            # other than in the public schema. Perhaps they should, as that
            # could be a nice way to get different behaviour per-tenant.
            return None, None
        if 'INDEX' in keywords and grouped[DDL][0] == 'DROP':
            # DROP INDEX does not have a table associated with it.
            # We will have to hit the database to see what tables have
            # an index with that name: we can just use the template/public
            # schemata though.
            return get_index_data(cursor, identifiers[0].get_name())[0], None
        if 'VIEW' in keywords or 'TABLE' in keywords:
            # We care about identifier 0, which will be the name of the view
            # or table.
            if identifiers:
                return identifiers[0].get_name(), identifiers[0].get_parent_name()
        elif 'TRIGGER' in keywords or 'INDEX' in keywords:
            # We care about identifier 1, as identifier 0 is the name of the
            # function or index: identifier 1 is the table it refers to.
            if len(identifiers) > 1:
                return identifiers[1].get_name(), identifiers[1].get_parent_name()

    # We also care about other non-DDL statements, as the implication is that
    # they should apply to every known schema, if we are updating as part of a
    # migration.
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
        execute = super(DatabaseSchemaEditor, self).execute

        table_name, schema_name = get_table_and_schema(sql, self.connection.cursor())

        # TODO: try to get the apps from current project_state, not global apps.
        if table_name and not schema_name and not is_shared_table(table_name):
            schema_aware_operation.send(
                self.__class__,
                db_table=table_name,
                function=execute,
                args=(sql, params)
            )
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
