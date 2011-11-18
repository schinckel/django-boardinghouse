from django.contrib import admin
from models import Schema

class SchemaAdmin(admin.ModelAdmin):
    pass

admin.site.register(Schema, SchemaAdmin)