# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os

from django.conf import settings
from django.db import migrations

with open(os.path.join(os.path.dirname(__file__), '..', 'sql', 'clone_schema.003.sql')) as fp:
    FORWARDS = fp.read()
with open(os.path.join(os.path.dirname(__file__), '..', 'sql', 'clone_schema.002.sql')) as fp:
    REVERSE = fp.read()

BUILD_DDL = """
SELECT 'ALTER SEQUENCE ' || quote_ident(schema_name) || '.' || quote_ident(sequence_name)
         || ' OWNED BY '   || quote_ident(schema_name) || '.'
         || quote_ident(MIN(table_name)) || '.' || quote_ident(MIN(column_name))
         || ';'
    FROM (
      SELECT table_schema AS schema_name,
             table_name,
             column_name,
             SUBSTRING(
               column_default
               FROM '^nextval\(''' || quote_ident(table_schema) || '\.(.*_seq)''::regclass\)'
             ) AS sequence_name
        FROM information_schema.columns
       WHERE table_schema = %s
         AND column_default LIKE 'nextval('''|| quote_ident(table_schema) || '%%''::regclass)'
    ) seq
GROUP BY sequence_name, schema_name
  HAVING COUNT(*) = 1
"""


def change_existing_sequence_owners(apps, schema_editor):
    alias = schema_editor.connection.alias
    cursor = schema_editor.connection.cursor()

    Schema = apps.get_model(*settings.BOARDINGHOUSE_SCHEMA_MODEL.split('.'))

    for schema in Schema.objects.using(alias).all():
        cursor.execute(BUILD_DDL, [schema.schema])
        for statement in cursor.fetchall():
            cursor.execute(statement[0])


class Migration(migrations.Migration):

    dependencies = [
        ('boardinghouse', '0003_update_clone_sql_function'),
    ]

    operations = [
        migrations.RunSQL(sql=FORWARDS, reverse_sql=REVERSE),
        migrations.RunPython(change_existing_sequence_owners),
    ]
