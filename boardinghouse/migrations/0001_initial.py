# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os

from django.conf import settings
from django.db import migrations

with open(os.path.join(os.path.dirname(__file__), '..', 'sql', 'clone_schema.001.sql')) as fp:
    CLONE_SCHEMA = fp.read()


class Migration(migrations.Migration):
    initial = True

    run_before = [
        migrations.swappable_dependency(settings.BOARDINGHOUSE_SCHEMA_MODEL),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    dependencies = []

    operations = [
        migrations.RunSQL(sql=CLONE_SCHEMA, reverse_sql='DROP FUNCTION clone_schema(text, text)'),
        migrations.RunSQL(sql='CREATE SCHEMA __template__', reverse_sql='DROP SCHEMA __template__ CASCADE'),
    ]
