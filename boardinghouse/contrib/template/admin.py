from django.contrib import admin

from .models import SchemaTemplate

admin.site.register(SchemaTemplate)


# Inject an action into the registered ModelAdmin for our Schema model.
def create_template_from_schema(modeladmin, request, queryset):
    for schema in queryset:
        template = SchemaTemplate(name=schema.name)
        template._clone = schema.schema
        template.save()
