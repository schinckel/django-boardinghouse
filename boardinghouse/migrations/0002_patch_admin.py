# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os

import django.core.validators
from django.conf import settings
from django.db import migrations, models

import boardinghouse
from boardinghouse.operations import AddField

with open(os.path.join(os.path.dirname(__file__), '..', 'sql', 'protect_schema_column.001.sql')) as fp:
    PROTECT_SCHEMA_COLUMN = fp.read()


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


def remove_all_schemata(apps, schema_editor):
    Schema = apps.get_model(*settings.BOARDINGHOUSE_SCHEMA_MODEL.split('.'))
    for schema in Schema.objects.all():
        schema.delete()


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        migrations.swappable_dependency(settings.BOARDINGHOUSE_SCHEMA_MODEL),
        # I really need to be able to ignore this dependency if django.contrib.admin
        # is not installed. Indeed, this whole migration needn't run if it isn't.
        ('admin', '0001_initial'),
        ('boardinghouse', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Schema',
            fields=[
                ('schema', models.CharField(primary_key=True, serialize=False, max_length=36, validators=[django.core.validators.RegexValidator(regex=r'^[a-z][a-z0-9_]*$', message='May only contain lowercase letters, digits and underscores. Must start with a letter.')], help_text='The internal name of the schema.<br>May only contain lowercase letters, digits and underscores. Must start with a letter.<br>May not be changed after creation.', unique=True)),
                ('name', models.CharField(help_text='The display name of the schema.', unique=True, max_length=128)),
                ('is_active', models.BooleanField(default=True, help_text='Use this instead of deleting schemata.')),
                ('users', models.ManyToManyField(help_text='Which users may access data from this schema.', related_name='schemata', to=settings.AUTH_USER_MODEL, blank=True)),
            ],
            options={
                'swappable': 'BOARDINGHOUSE_SCHEMA_MODEL',
                'verbose_name_plural': 'schemata',
            },
            bases=(boardinghouse.base.SharedSchemaMixin, models.Model),
        ),

        migrations.RunPython(code=lambda apps, schema_editor: None, reverse_code=remove_all_schemata),

        AddField(
            app_label='admin',
            model_name='logentry',
            name='object_schema_id',
            field=models.TextField(blank=True, null=True),
            preserve_default=True,
        ),
        ProtectSchemaColumn(),
    ]
