from django import forms

from .models import DemoSchema, ValidDemoTemplate


class CreateDemoForm(forms.ModelForm):
    from_template = forms.ModelChoiceField(ValidDemoTemplate.objects.all())

    class Meta:
        model = DemoSchema
        fields = ('from_template',)

    def save(self, commit=True):
        self.instance._clone = self.cleaned_data['from_template'].template_schema.schema
        return super(CreateDemoForm, self).save(commit)
