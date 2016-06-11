from django import forms

from .models import DemoSchema


class CreateDemoForm(forms.ModelForm):
    class Meta:
        model = DemoSchema
        fields = ('from_template',)
