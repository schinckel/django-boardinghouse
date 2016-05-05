# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations
from django.apps import apps as global_apps


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
        "CREATE OR REPLACE FUNCTION noop() RETURNS TRIGGER AS 'BEGIN RETURN NEW; END;' LANGUAGE plpgsql;")
    # We can't use the supplied apps, because we aren't in it yet?
    app_config = global_apps.get_app_config('groups')
    for model in app_config.required_public_views:
        schema_editor.execute(view_from_model(model, schema_editor.connection))


def drop_views(apps, schema_editor):
    app_config = global_apps.get_app_config('groups')
    for model in app_config.required_public_views:
        schema_editor.execute('DROP VIEW "{public}"."{table_name}" CASCADE'.format(
            public=settings.PUBLIC_SCHEMA, table_name=model._meta.db_table
        ))


class Migration(migrations.Migration):
    initial = True

    runs_before = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    dependencies = []

    operations = [
        migrations.RunPython(create_views, drop_views)
    ]
