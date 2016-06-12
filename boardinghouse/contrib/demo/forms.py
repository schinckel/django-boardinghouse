from django import forms

from .models import DemoSchema


class CreateDemoForm(forms.ModelForm):
    """Create a new DemoSchema object.

    Does not allow passing in a user or expiry: those should be set in the view,
    or use the defaults in the latter case.
    """
    class Meta:
        model = DemoSchema
        fields = ('from_template',)
