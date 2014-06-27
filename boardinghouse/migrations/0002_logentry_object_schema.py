# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

class AddField(migrations.AddField):
    def __init__(self, app_label, *args, **kwargs):
        self.app_label = app_label
        super(AddField, self).__init__(*args, **kwargs)

    def state_forwards(self, app_label, state):
        return super(AddField, self).state_forwards(self.app_label, state)

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        return super(AddField, self).database_forwards(self.app_label, schema_editor, from_state, to_state)

    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        return super(AddField, self).database_backwards(self.app_label, schema_editor, from_state, to_state)


class Migration(migrations.Migration):

    dependencies = [
        ('admin', '0001_initial'),
        ('boardinghouse', '0001_initial'),
    ]

    operations = [
        AddField(
            app_label='admin',
            model_name='logentry',
            name='object_schema',
            field=models.ForeignKey(blank=True, to='boardinghouse.Schema', null=True),
            preserve_default=True,
        ),
    ]
