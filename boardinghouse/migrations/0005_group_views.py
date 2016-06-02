# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations

from boardinghouse.schema import _table_exists
from boardinghouse.signals import schema_aware_operation


def private_auth_models(apps):
    """
    Which of the django.contrib.auth models should be private, and more specifically, should
    also have an (empty) VIEW inside settings.PUBLIC_SCHEMA, so we don't get exceptions when
    no schema is activated.

    Note this takes into account the settings.PRIVATE_MODELS, to allow us to use the one
    migration for when `boardinghouse.contrib.groups` is installed (or auth.group is added
    by other means).
    """
    User = apps.get_model(*settings.AUTH_USER_MODEL.split('.'))

    models = [User.groups.through, User.user_permissions.through]

    if 'auth.groups' in settings.PRIVATE_MODELS:
        models.append(apps.get_model('auth', 'group'))

    return models


def view_from_model(model):
    """
    Return a DDL statement that creates a VIEW based on the model.

    The view MUST always return an empty query, and writes to the view should be
    silently discarded without error.
    """
    return '''CREATE VIEW "{public}"."{table_name}" AS (SELECT * FROM "{template}"."{table_name}" WHERE false);

              CREATE TRIGGER "{table_name}_noop"
              INSTEAD OF INSERT ON "{public}"."{table_name}"
              FOR EACH ROW EXECUTE PROCEDURE noop()'''.format(public=settings.PUBLIC_SCHEMA,
                                                              template=settings.TEMPLATE_SCHEMA,
                                                              table_name=model._meta.db_table)


def create_views(apps, schema_editor):
    # We need a noop() function in the database, to use as our INSTEAD OF INSERT trigger.
    schema_editor.execute(
        "CREATE OR REPLACE FUNCTION noop() RETURNS TRIGGER AS 'BEGIN RETURN NEW; END;' LANGUAGE plpgsql;"
    )

    for model in private_auth_models(apps):
        schema_editor.execute(view_from_model(model))


def drop_views(apps, schema_editor):
    for model in private_auth_models(apps):
        schema_editor.execute('DROP VIEW "{public}"."{table_name}" CASCADE'.format(
            public=settings.PUBLIC_SCHEMA, table_name=model._meta.db_table
        ))


def move_existing_to_schemata(apps, schema_editor):
    """
    This is not really working that well at the moment. Perhaps we should look at
    using the migration operations that actually add/remove these tables?

    Or maybe just give instructions about what to do if this case is detected?
    """
    def move_table(table_name):
        schema_editor.execute('CREATE TABLE "{table}" (LIKE "{public}"."{table}" INCLUDING ALL)'.format(
            public=settings.PUBLIC_SCHEMA,
            table=table_name
        ))

    for model in private_auth_models(apps):
        # Look for model in public schema.
        table_name = model._meta.db_table
        if (
            _table_exists(schema=settings.PUBLIC_SCHEMA, table_name=table_name) and
            not _table_exists(schema=settings.TEMPLATE_SCHEMA, table_name=table_name)
        ):
            schema_aware_operation.send(schema_editor,
                                        db_table=table_name,
                                        function=move_table,
                                        args=(table_name,))
            # Now we need to delete the table from the public schema.
            schema_editor.execute(
                'ALTER TABLE "{public}"."{table}" RENAME TO ____{table}'.format(public=settings.PUBLIC_SCHEMA,
                                                                                table=table_name))


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
