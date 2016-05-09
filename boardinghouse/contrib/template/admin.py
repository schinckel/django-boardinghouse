from django.contrib import admin
from django.utils.translation import ugettext as _

from .models import SchemaTemplate

admin.site.register(SchemaTemplate)


# Inject an action into the registered ModelAdmin for our Schema model.
def create_template_from_schema(modeladmin, request, queryset):
    created = []
    for schema in queryset:
        template = SchemaTemplate(name=schema.name)
        template._clone = schema.schema
        template.save()
        created.append(template.name)

    if len(created) == 1:
        modeladmin.message_user(request,
                                message=_('Created one new template: "{}"').format(*created),
                                level='success')
    elif len(created) > 1:
        modeladmin.message_user(request,
                                message=_('Created {} new templates: {}').format(len(created), ', '.join(created)),
                                level='success')
