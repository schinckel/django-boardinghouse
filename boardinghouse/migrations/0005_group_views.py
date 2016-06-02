# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations

from boardinghouse.schema import _table_exists
from boardinghouse.signals import schema_aware_operation


def view_from_model(model, connection):
    view_parts = [
        'CREATE VIEW "{public}"."{table_name}" AS (SELECT '.format(
            public=settings.PUBLIC_SCHEMA, table_name=model._meta.db_table
        ),
    ]
    for field in model._meta.fields:
        view_parts.append('NULL::INTEGER AS "{column}",'.format(
            db_type=field.db_type(connection), column=field.db_column or field.attname
        ))
    # Remove the comma off the last one.
    view_parts[-1] = view_parts[-1][:-1]
    view_parts.append(');')
    view_parts.extend([
        'CREATE TRIGGER "{table_name}_noop" INSTEAD OF INSERT ON "{public}"."{table_name}"'.format(
            public=settings.PUBLIC_SCHEMA, table_name=model._meta.db_table
        ),
        'FOR EACH ROW EXECUTE PROCEDURE noop();'
    ])
    return '\n'.join(view_parts)


def create_views(apps, schema_editor):

    schema_editor.execute(
        "CREATE OR REPLACE FUNCTION noop() RETURNS TRIGGER AS 'BEGIN RETURN NEW; END;' LANGUAGE plpgsql;"
    )
    User = apps.get_model(*settings.AUTH_USER_MODEL.split('.'))

    # We can't use the supplied apps, because we aren't in it yet?
    for model in [User.groups.through, User.user_permissions.through]:
        schema_editor.execute(view_from_model(model, schema_editor.connection))


def drop_views(apps, schema_editor):
    User = apps.get_model(*settings.AUTH_USER_MODEL.split('.'))

    for model in [User.groups.through, User.user_permissions.through]:
        schema_editor.execute('DROP VIEW "{public}"."{table_name}" CASCADE'.format(
            public=settings.PUBLIC_SCHEMA, table_name=model._meta.db_table
        ))


def move_existing_to_schemata(apps, schema_editor):
    User = apps.get_model(*settings.AUTH_USER_MODEL.split('.'))

    def move_table(table_name):
        schema_editor.execute('CREATE TABLE "{table}" (LIKE "{public}"."{table}" INCLUDING ALL)'.format(
            public=settings.PUBLIC_SCHEMA,
            table=table_name
        ))

    for model in [User.groups.through, User.user_permissions.through]:
        # Look for model in public schema.
        table_name = model._meta.db_table
        if _table_exists(schema=settings.PUBLIC_SCHEMA, table_name=table_name):
            schema_aware_operation.send(
                schema_editor,
                db_table=table_name,
                function=move_table,
                args=(table_name,)
            )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('boardinghouse', '0004_change_sequence_owners'),
    ]

    operations = [
        # We need to look and see if we have the tables that we are expecting to have as private relations,
        # but in the public schema. If we do, then we need to drop them, and create empty versions in all
        # schemata (template and otherwise). The reverse of this is a noop, because we don't support the erroneous
        # state that existed before.
        migrations.RunPython(move_existing_to_schemata, noop),
        # Then we need to create the views, to prevent exceptions when querying for permissions without an active
        # schema.
        migrations.RunPython(create_views, drop_views),
    ]
