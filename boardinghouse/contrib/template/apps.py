from django.apps import AppConfig
from django.conf import settings


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
            module = __import__(Schema.__module__.rsplit('.', 1)[0] + '.admin')
            BaseSchemaAdmin = module.admin.admin.site._registry[Schema].__class__

            from django.contrib import admin
            from django import forms

            admin.site.unregister(Schema)

            class SchemaAdmin(BaseSchemaAdmin):
                actions = [create_template_from_schema]

                def get_form(self, request, obj=None, **kwargs):
                    if not obj and 'boardinghouse.contrib.template' in settings.INSTALLED_APPS:
                        class form(forms.ModelForm):
                            clone_schema = forms.ModelChoiceField(required=False, queryset=SchemaTemplate.objects.all())
                    else:
                        class form(forms.ModelForm):
                            pass
                    kwargs['form'] = form
                    return super(SchemaAdmin, self).get_form(request, obj, **kwargs)

                def get_fields(self, request, obj):
                    fields = super(SchemaAdmin, self).get_fields(request, obj)
                    if 'clone_schema' in fields:
                        fields.remove('clone_schema')
                        return ['clone_schema'] + fields
                    return fields

                def save_model(self, request, obj, form, change):
                    if not change and form.cleaned_data.get('clone_schema', None) is not None:
                        obj._clone = form.cleaned_data['clone_schema'].schema
                    return super(SchemaAdmin, self).save_model(request, obj, form, change)

            admin.site.register(Schema, SchemaAdmin)
