from django.contrib import admin

from .schema import get_active_schema, is_shared_model

# We only want to install our SchemaAdmin if our schema model is the
# one that is used: otherwise it's up to the project developer to
# add it to the admin, if they want it.
from .models import Schema


class SchemaAdmin(admin.ModelAdmin):
    def get_readonly_fields(self, request, obj=None):
        """
        Prevents `schema` from being editable once created.
        """
        if obj is not None:
            return ('schema',)
        return ()

    filter_horizontal = ('users',)

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
