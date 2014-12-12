# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os

from django.db import models, migrations
from django.conf import settings

from boardinghouse.operations import AddField, LoadSQLFromScript

PROTECT_SCHEMA_COLUMN = os.path.join(os.path.dirname(__file__), '..', 'sql', 'protect_schema_column.sql')


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        migrations.swappable_dependency(getattr(settings, 'BOARDINGHOUSE_SCHEMA_MODEL', 'boardinghouse.Schema')),
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
            field=models.ForeignKey(blank=True, to=getattr(settings, 'BOARDINGHOUSE_SCHEMA_MODEL', 'boardinghouse.Schema'), null=True),
            preserve_default=True,
        ),
        LoadSQLFromScript(PROTECT_SCHEMA_COLUMN)
    ]
