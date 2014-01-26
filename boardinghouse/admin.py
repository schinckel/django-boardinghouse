"""
.. autoclass:: SchemaAdmin
.. autofunction:: schemata

"""
from django.contrib import admin

from .models import Schema

class SchemaAdmin(admin.ModelAdmin):
    """
    prevents `schema` from being editable once created.
    """
    def get_readonly_fields(self, request, obj=None):
        if obj is not None:
            return ('schema',)
        return ()

admin.site.register(Schema, SchemaAdmin)

def schemata(obj):
    """
    Usable function for adding schemata representation to admin
    list view.
    """
    return '<br>'.join(obj.schemata.values_list('name', flat=True))
schemata.allow_tags = True