# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Schema',
            fields=[
                ('schema', models.CharField(primary_key=True, serialize=False, max_length=36, validators=[django.core.validators.RegexValidator(regex=b'^[a-z][a-z0-9_]*$', message='May only contain lowercase letters, digits and underscores. Must start with a letter.')], help_text='The internal name of the schema.<br>May only contain lowercase letters, digits and underscores. Must start with a letter.<br>May not be changed after creation.', unique=True)),
                ('name', models.CharField(help_text='The display name of the schema.', unique=True, max_length=128)),
                ('is_active', models.BooleanField(default=True, help_text='Use this instead of deleting schemata.')),
                ('users', models.ManyToManyField(to=settings.AUTH_USER_MODEL, null=True, blank=True)),
            ],
            options={
                'verbose_name_plural': b'schemata',
            },
            bases=(models.Model,),
        ),
    ]
