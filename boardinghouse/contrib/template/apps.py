from importlib import import_module

from django.apps import AppConfig
from django.conf import settings
from django.core.checks import Error, register


class BoardingHouseTemplateConfig(AppConfig):
    name = 'boardinghouse.contrib.template'

    def ready(self):
        if not hasattr(settings, 'BOARDINGHOUSE_TEMPLATE_PREFIX'):
            settings.BOARDINGHOUSE_TEMPLATE_PREFIX = '__tmpl_'

        from boardinghouse.schema import get_schema_model

        from .models import SchemaTemplate
        from ..template import receivers  # NOQA

        if 'django.contrib.admin' in settings.INSTALLED_APPS:
            # We can't just add the action to the SchemaAdmin, because that may not be a subclass of ModelAdmin,
            # in which case the action would be applied to all models.
            from .admin import create_template_from_schema
            Schema = get_schema_model()
            module = import_module(Schema.__module__.rsplit('.', 1)[0] + '.admin')
            BaseSchemaAdmin = module.admin.site._registry[Schema].__class__

            from django.contrib import admin
            from django import forms

            admin.site.unregister(Schema)

            class SchemaAdmin(BaseSchemaAdmin):
                actions = list(BaseSchemaAdmin.actions or []) + [create_template_from_schema]

                def get_form(self, request, obj=None, **kwargs):
                    if not obj and 'boardinghouse.contrib.template' in settings.INSTALLED_APPS:
                        class SchemaAdminForm(BaseSchemaAdmin.form or forms.ModelForm):
                            clone_schema = forms.ModelChoiceField(required=False,
                                                                  queryset=SchemaTemplate.objects.all())
                        kwargs['form'] = SchemaAdminForm
                    return super(SchemaAdmin, self).get_form(request, obj, **kwargs)

                def get_fields(self, request, obj):
                    fields = super(SchemaAdmin, self).get_fields(request, obj)
                    if 'clone_schema' in fields:
                        fields.remove('clone_schema')
                        return ['clone_schema'] + fields
                    return fields

                def save_model(self, request, obj, form, change):
                    if not change and form.cleaned_data.get('clone_schema') is not None:
                        obj._clone = form.cleaned_data['clone_schema'].schema
                    return super(SchemaAdmin, self).save_model(request, obj, form, change)

            admin.site.register(Schema, SchemaAdmin)


@register('settings')
def check_template_prefix_stats_with_underscore(app_configs=None, **kwargs):
    """Ensure that the prefix for schema template internal names starts with underscore.

    This is required because a leading underscore is the trigger that the indicated
    schema is not a "regular" schema, and should not be activated according to the
    normal rules.
    """
    from django.conf import settings

    if not settings.BOARDINGHOUSE_TEMPLATE_PREFIX.startswith('_'):
        return [Error('BOARDINGHOUSE_TEMPLATE_PREFIX must start with an underscore',
                      id='boardinghouse.contrib.template.E001')]

    return []
