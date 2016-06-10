from django.views.generic import CreateView

from .forms import CreateDemoForm


class CreateDemo(CreateView):
    form_class = CreateDemoForm


def delete_demo(DeleteView):
    pass


def refresh_demo(request):
    # Hmm. Did we store the one we cloned?
    pass
