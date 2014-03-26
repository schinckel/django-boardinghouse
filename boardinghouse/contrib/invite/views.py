from django.views import generic

from .forms import InvitePersonForm, AcceptForm, DeclineForm


class UserMixin(object):
    def get_form_kwargs(self):
        kwargs = super(UserMixin, self).get_form_kwargs()
        kwargs.update(user=self.request.user)
        return kwargs


class InvitePerson(UserMixin, generic.CreateView):
    form_class = InvitePersonForm
    template_name = 'invite/new.html'
    
    def get_success_url(self):
        return '/admin/invite/invitation/'

invite_person = InvitePerson.as_view()


class InvitationCreated(generic.TemplateView):
    template_name = 'base.html'