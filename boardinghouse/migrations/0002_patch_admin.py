# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os

from django.db import models, migrations
from django.conf import settings

from boardinghouse.operations import AddField

PROTECT_SCHEMA_COLUMN = open(os.path.join(os.path.dirname(__file__),
    '..', 'sql', 'protect_schema_column.001.sql')).read()


class ProtectSchemaColumn(migrations.RunSQL):
    def __init__(self, *args, **kwargs):
        self.sql = ''
        self.reverse_sql = 'DROP FUNCTION reject_schema_column_change() CASCADE'
        self.state_operations = []
        self.hints = {}

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        schema_model = from_state.apps.get_model(settings.BOARDINGHOUSE_SCHEMA_MODEL)
        self.sql = PROTECT_SCHEMA_COLUMN.format(schema_model=schema_model._meta.db_table,
                                                public_schema=settings.PUBLIC_SCHEMA)
        super(ProtectSchemaColumn, self).database_forwards(app_label, schema_editor, from_state, to_state)


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        migrations.swappable_dependency(settings.BOARDINGHOUSE_SCHEMA_MODEL),
        # I really need to be able to ignore this dependency if django.contrib.admin
        # is not installed. Indeed, this whole migration needn't run if it isn't.
        ('admin', '0001_initial'),
        ('boardinghouse', '0001_initial'),
    ]

    operations = [
        AddField(
            app_label='admin',
            model_name='logentry',
            name='object_schema',
            field=models.ForeignKey(blank=True, to=settings.BOARDINGHOUSE_SCHEMA_MODEL, null=True),
            preserve_default=True,
        ),
        ProtectSchemaColumn(),
    ]
