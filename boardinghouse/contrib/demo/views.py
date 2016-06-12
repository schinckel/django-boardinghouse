"""
"""
import json

try:
    from django.contrib.auth.mixins import LoginRequiredMixin
except ImportError:
    from braces.views import LoginRequiredMixin
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _
from django.views.generic import View
from django.views.generic.edit import DeleteView, BaseCreateView

from .forms import CreateDemoForm
from .models import DemoSchema


class DemoSchemaMixin(LoginRequiredMixin):
    def get_object(self, queryset=None):
        return get_object_or_404(DemoSchema, user=self.request.user)

    def get_success_url(self):
        return (
            self.request.POST.get('redirect-to', None) or
            self.request.GET.get('redirect-to', None) or
            '/__change_schema__/{}/'.format(self.object.schema)
        )


class CreateDemo(DemoSchemaMixin, BaseCreateView):
    """Create a new Demo for the logged in user.

    Use the provided template, and the default expiry period.
    """
    form_class = CreateDemoForm

    def form_invalid(self, form):
        return HttpResponse(json.dumps({'errors': form.errors}), status=409)

    def form_valid(self, form):
        if DemoSchema.objects.filter(user=self.request.user).exists():
            form.add_error(None, _('Creating a demo when one already exists is not permitted'))
            return self.form_invalid(form)

        form.instance.user = self.request.user
        return super(CreateDemo, self).form_valid(form)


class DeleteDemo(DemoSchemaMixin, DeleteView):
    """Delete the Demo for the logged in user."""


class ResetDemo(DemoSchemaMixin, View):
    """Reset the Demo for the logged in user back to the clean template."""
    def post(self, request, *args, **kwargs):
        # Just use the raw drop/create functions? At this stage, it's simpler (and safer?) to
        # delete the existing DemoSchema object, and create a new one. We reset the demo period,
        # but use the same template.
        demo_schema = self.get_object()
        demo_schema.delete()
        self.object = DemoSchema.objects.create(
            user=self.request.user,
            from_template=demo_schema.from_template
        )
        return HttpResponseRedirect(self.get_success_url())
