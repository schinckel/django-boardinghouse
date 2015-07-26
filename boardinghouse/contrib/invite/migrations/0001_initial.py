# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import boardinghouse.base


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        migrations.swappable_dependency(settings.BOARDINGHOUSE_SCHEMA_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Invitation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('email', models.EmailField(max_length=254, verbose_name='Email address')),
                ('message', models.TextField()),
                ('redemption_code', models.UUIDField(null=True, blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('accepted_at', models.DateTimeField(null=True, blank=True)),
                ('declined_at', models.DateTimeField(null=True, blank=True)),
                ('accepted_by', models.ForeignKey(related_name='accepted_invitations', to=settings.AUTH_USER_MODEL, null=True, blank=True)),
                ('schema', models.ForeignKey(related_name='invitations', to=settings.BOARDINGHOUSE_SCHEMA_MODEL)),
                ('sender', models.ForeignKey(related_name='sent_invitations', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('created_at',),
            },
            bases=(boardinghouse.base.SharedSchemaMixin, models.Model),
        ),
        # Only one of accepted_at, declined_at may be non-null.
        migrations.RunSQL(
            sql='ALTER TABLE invite_invitation ADD CONSTRAINT only_one_of_accept_deny CHECK (accepted_at is NULL or declined_at IS NULL)',
            reverse_sql='ALTER TABLE invite_invitation DROP CONSTRAINT only_one_of_accept_deny'
        ),
        # Ensure accepted_at/accepted_by
        migrations.RunSQL(
            sql='ALTER TABLE invite_invitation ADD CONSTRAINT accepted_at_and_accepted_by CHECK ((accepted_by_id IS NULL AND accepted_at IS NULL) or (accepted_at IS NOT NULL AND accepted_by_id IS NOT NULL))',
            reverse_sql='ALTER TABLE invite_invitation DROP CONSTRAINT accepted_at_and_accepted_by'
        ),
    ]
