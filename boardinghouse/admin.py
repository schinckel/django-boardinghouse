from django.contrib import admin, auth
from django.http import Http404

from .models import Schema

class SchemaAdmin(admin.ModelAdmin):
    
    def get_readonly_fields(self, request, obj=None):
        if obj is not None:
            return ('schema',)
        return ()

admin.site.register(Schema, SchemaAdmin)

def schemata(obj):
    return '<br>'.join(obj.schemata.values_list('name', flat=True))
schemata.allow_tags = True