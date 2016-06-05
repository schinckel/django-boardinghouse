from django import forms
from django.contrib import admin
from django.utils.timesince import timesince, timeuntil

from .models import DemoSchema, ValidDemoTemplate


@admin.register(DemoSchema)
class DemoSchemaAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'expires_at',
        'valid',
        'expires_in',
        'expired_ago',
    ]

    def valid(self, obj):
        return not obj.expired
    valid.boolean = True

    def expires_in(self, obj):
        if not obj.expired:
            return timeuntil(obj.expires_at)

    def expired_ago(self, obj):
        if obj.expired:
            return timesince(obj.expires_at)

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['user']
        return []

    def get_form(self, request, obj=None, **kwargs):
        class DemoForm(forms.ModelForm):
            expires_at = forms.DateTimeField(required=False)

            if obj is None:
                from_template = forms.ModelChoiceField(ValidDemoTemplate.objects.all())

            class Meta:
                model = DemoSchema
                if obj is None:
                    fields = ('user', 'expires_at', 'from_template')
                else:
                    fields = ('expires_at', )

            def save(form, commit=True):
                if not form.instance.pk:
                    form.instance._clone = form.cleaned_data['from_template'].template_schema.schema
                return super(DemoForm, form).save(commit)

        return DemoForm


# Inject an inline to allow marking as valid for demo.
class ValidDemoInline(admin.StackedInline):
    model = ValidDemoTemplate
    can_delete = False
    template = 'admin/edit_inline/use-for-demo.html'

    class form(forms.ModelForm):
        use_for_demo = forms.BooleanField(initial=False, required=False)

        class Meta:
            model = ValidDemoTemplate
            fields = ('use_for_demo',)

        def __init__(self, *args, **kwargs):
            super(ValidDemoInline.form, self).__init__(*args, **kwargs)
            if self.instance.pk:
                self.initial['use_for_demo'] = True

        def save(self, commit=True):
            if self.cleaned_data.get('use_for_demo', False):
                return super(ValidDemoInline.form, self).save(commit)
            elif self.instance.pk and commit:
                self.instance.delete()
                return self.instance


def use_for_demo(obj):
    return bool(obj.use_for_demo)
use_for_demo.empty_value_display = False
use_for_demo.boolean = True

SchemaTemplate = ValidDemoTemplate._meta.pk.rel.to
SchemaTemplateAdmin = admin.site._registry[SchemaTemplate].__class__
SchemaTemplateAdmin.inlines.append(ValidDemoInline)

SchemaTemplateAdmin.list_display.append(use_for_demo)
