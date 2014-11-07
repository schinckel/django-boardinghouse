# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import boardinghouse.base


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='TemplateSchema',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=128)),
            ],
            options={
                'default_permissions': (b'add', b'change', b'delete', b'view', b'activate'),
                'verbose_name_plural': 'template schemata',
            },
            bases=(boardinghouse.base.SharedSchemaMixin, models.Model),
        ),
    ]
