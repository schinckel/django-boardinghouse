"""

"""
from __future__ import unicode_literals

import django
from django.contrib import admin
from django.contrib.admin.models import LogEntry, LogEntryManager
from django.db import models
from django.db.models import expressions, Q
from django.dispatch import receiver

from .models import Schema
from .schema import get_active_schema_name, get_schema_model, is_shared_model
from .signals import find_schema


class SchemaAdmin(admin.ModelAdmin):
    """
    The `ModelAdmin` for the schema class should protect the `schema`
    field, but only once the object has been saved.
    """
    def get_readonly_fields(self, request, obj=None):
        """
        Prevents `schema` from being editable once created.
        """
        if obj is not None:
            return ('schema',)
        return ()

    filter_horizontal = ('users',)
    actions = []

# We only want to install our SchemaAdmin if our schema model is the
# one that is used: otherwise it's up to the project developer to
# add it to the admin, if they want it.
if get_schema_model() == Schema:
    admin.site.register(Schema, SchemaAdmin)


def schemata(obj):
    """
    Useful function for adding schemata representation to admin
    list view.
    """
    return '<br>'.join([s.name for s in obj.schemata.all()])

schemata.allow_tags = True


def get_inline_instances(self, request, obj=None):
    """
    Prevent the display of non-shared inline objects associated
    with private models if no schema is currently selected.

    If we don't patch this, then a ``DatabaseError`` will occur because
    the tables could not be found.
    """
    schema = get_active_schema_name()
    return [
        inline(self.model, self.admin_site) for inline in self.inlines
        if schema or is_shared_model(inline.model)
    ]


admin.ModelAdmin.get_inline_instances = get_inline_instances

if not getattr(LogEntry, 'object_schema', None):
    # We can't use a proper foreign key, as it plays havoc with migrations.
    LogEntry.add_to_class(
        'object_schema_id',
        models.TextField(blank=True, null=True)
    )

    @receiver(models.signals.pre_save, sender=LogEntry)
    def update_object_schema(sender, instance, **kwargs):
        obj = instance.get_edited_object()

        if not is_shared_model(obj):
            instance.object_schema_id = obj._schema

    get_admin_url = LogEntry.get_admin_url

    def get_admin_url_with_schema(self):
        url = get_admin_url(self)

        if self.object_schema_id and url:
            return '{0}?__schema={1}'.format(url, self.object_schema_id)

        return url

    LogEntry.get_admin_url = get_admin_url_with_schema

    SchemaModel = get_schema_model()

    def object_schema(self):
        for handler, response in find_schema.send(sender=None, schema=self.object_schema_id):
            if response:
                return response

    LogEntry.object_schema = property(object_schema)

    def get_queryset(self):
        queryset = super(LogEntryManager, self).get_queryset()

        if django.VERSION < (1, 8):
            return queryset.extra(where=['object_schema_id = current_schema() OR object_schema_id IS NULL'])

        return queryset.filter(Q(object_schema_id=None) |
                               Q(object_schema_id=expressions.RawSQL('current_schema()', [])))

    LogEntryManager.get_queryset = get_queryset
