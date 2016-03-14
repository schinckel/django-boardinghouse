# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os

from django.db import models, migrations
from django.conf import settings
import django.core.validators
import boardinghouse.base

CLONE_SCHEMA = open(os.path.join(os.path.dirname(__file__), '..', 'sql', 'clone_schema.001.sql')).read()


def remove_all_schemata(apps, schema_editor):
    Schema = apps.get_model(*settings.BOARDINGHOUSE_SCHEMA_MODEL.split('.'))
    db_alias = schema_editor.connection.alias
    sql = ';'.join([
        'DROP SCHEMA {} CASCADE'.format(schema.schema)
        for schema in Schema.objects.using(db_alias).all()
    ])
    schema_editor.connection.cursor().execute(sql)


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        migrations.swappable_dependency(settings.BOARDINGHOUSE_SCHEMA_MODEL),
        ('admin', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(sql=CLONE_SCHEMA, reverse_sql='DROP FUNCTION clone_schema(text, text)'),
        migrations.RunSQL(sql='CREATE SCHEMA __template__', reverse_sql='DROP SCHEMA __template__ CASCADE'),

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

    ]
