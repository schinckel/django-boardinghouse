# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os

from django.db import migrations
from django.conf import settings

with open(os.path.join(os.path.dirname(__file__), '..', 'sql', 'clone_schema.002.sql')) as fp:
    FORWARDS = fp.read()
with open(os.path.join(os.path.dirname(__file__), '..', 'sql', 'clone_schema.001.sql')) as fp:
    REVERSE = fp.read()


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        migrations.swappable_dependency(settings.BOARDINGHOUSE_SCHEMA_MODEL),
        ('boardinghouse', '0002_patch_admin'),
    ]

    operations = [
        migrations.RunSQL(sql=FORWARDS, reverse_sql=REVERSE)
    ]
