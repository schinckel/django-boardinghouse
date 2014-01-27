"""
"""
from django.contrib import admin

from .models import Schema
from .schema import get_schema, is_shared_model, get_schema_model

class SchemaAdmin(admin.ModelAdmin):
    """
    prevents `schema` from being editable once created.
    """
    def get_readonly_fields(self, request, obj=None):
        if obj is not None:
            return ('schema',)
        return ()

if get_schema_model() == Schema:
    admin.site.register(Schema, SchemaAdmin)

def schemata(obj):
    """
    Usable function for adding schemata representation to admin
    list view.
    """
    return '<br>'.join(obj.schemata.values_list('name', flat=True))
schemata.allow_tags = True

def get_inline_instances(self, request, obj=None):
    schema = get_schema()
    return [
        inline for inline in self.inlines
        if schema or is_shared_model(inline.model)
    ]

admin.ModelAdmin.get_inline_instances = get_inline_instances