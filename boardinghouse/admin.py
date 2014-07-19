"""

"""
from __future__ import unicode_literals

from django.conf import settings
from django.contrib import admin

from .models import Schema
from .schema import get_active_schema, is_shared_model, get_schema_model


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
    with _every_ model if no schema is currently selected.

    If we don't patch this, then a ``DatabaseError`` will occur because
    the tables could not be found.
    """
    schema = get_active_schema()
    return [
        inline(self.model, self.admin_site) for inline in self.inlines
        if schema or is_shared_model(inline.model)
    ]


admin.ModelAdmin.get_inline_instances = get_inline_instances


from django.contrib.admin.models import LogEntry
from django.db import models
from django.dispatch import receiver

if not getattr(LogEntry, 'object_schema', None):
    LogEntry.add_to_class(
        'object_schema',
        models.ForeignKey(getattr(settings, 'BOARDINGHOUSE_SCHEMA_MODEL', 'boardinghouse.Schema'), blank=True, null=True)
    )

    @receiver(models.signals.pre_save, sender=LogEntry)
    def update_object_schema(sender, instance, **kwargs):
        obj = instance.get_edited_object()

        if not is_shared_model(obj):
            instance.object_schema_id = obj._schema

    get_admin_url = LogEntry.get_admin_url

    def get_admin_url_with_schema(self):
        if self.object_schema_id:
            return get_admin_url(self) + '?__schema=%s' % self.object_schema_id

        return get_admin_url(self)

    LogEntry.get_admin_url = get_admin_url_with_schema
