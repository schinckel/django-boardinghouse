from django.contrib import admin
from django.conf import settings

from .schema import get_schema, is_shared_model, get_schema_model

# We only want to install our SchemaAdmin if our schema model is the
# one that is used: otherwise it's up to the project developer to 
# add it to the admin, if they want it.
if settings.SCHEMA_MODEL.lower() == 'boardinghouse.schema':
    from .models import Schema
    
    class SchemaAdmin(admin.ModelAdmin):
        def get_readonly_fields(self, request, obj=None):
            """
            Prevents `schema` from being editable once created.
            """
            if obj is not None:
                return ('schema',)
            return ()

    admin.site.register(Schema, SchemaAdmin)

def schemata(obj):
    """
    Useful function for adding schemata representation to admin
    list view.
    """
    return '<br>'.join(obj.schemata.values_list('name' , flat=True))
schemata.allow_tags = True

def get_inline_instances(self, request, obj=None):
    """
    Prevent the display of non-shared inline objects associated
    with _every_ model if no schema is currently selected.
    
    If we don't patch this, then a ``DatabaseError`` will occur because
    the tables could not be found.
    """
    schema = get_schema()
    return [
        inline for inline in self.inlines
        if schema or is_shared_model(inline.model)
    ]

admin.ModelAdmin.get_inline_instances = get_inline_instances