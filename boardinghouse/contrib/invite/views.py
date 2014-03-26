from django.views import generic

from .forms import InvitePersonForm, AcceptForm, DeclineForm
from .models import Invitation

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


class ViewInvitation(generic.DetailView):
    
    def get_object(self):
        return Invitation.objects.get(**self.kwargs)
    
    def get_template_names(self):
        if self.object.redeemed:
            return 'invite/redeemed.html'
        if self.object.expired:
            return 'invite/expired.html'
        return 'invite/view.html'

view_invitation = ViewInvitation.as_view()