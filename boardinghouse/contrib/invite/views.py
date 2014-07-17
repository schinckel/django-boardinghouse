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
    # Hmm. We really need a reverse_lazy here, methinks.
    success_url = '/admin/invite/invitation/'

invite_person = InvitePerson.as_view()


class InvitationMixin(object):
    redeemed_template_name = 'invite/redeemed.html'
    expired_template_name = 'invite/expired.html'

    def get_object(self):
        return Invitation.objects.get(**self.kwargs)

    def get_template_names(self):
        if self.object.redeemed:
            return self.redeemed_template_name
        if self.object.expired:
            return self.expired_template_name
        return [self.template_name]


class ViewInvitation(InvitationMixin, generic.DetailView):
    template_name = 'invite/view.html'

view_invitation = ViewInvitation.as_view()


class AcceptInvitation(ViewInvitation):
    template_name = 'invite/confirm.html'

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(AcceptInvitation, self).get_context_data(**kwargs)
        # Need to do this, in case RequestContext is not in context processors.
        context['logged_in'] = not self.request.user.is_anonymous()
        return context
    # Maybe have the accept-with-this-account, login-and-accept, register-new-account forms as options?

accept_invitation = AcceptInvitation.as_view()


class ConfirmInvitation(InvitationMixin, UserMixin, generic.UpdateView):
    form_class = AcceptForm
    success_url = '/admin/invite/invitation/'

confirm_invitation = ConfirmInvitation.as_view()


class LoginAndAcceptView(object):
    pass


class RegisterAndAcceptView(object):
    pass


class DeclineInvitation(InvitationMixin, generic.UpdateView):
    form_class = DeclineForm
    success_url = '/admin/invite/invitation/'

decline_invitation = DeclineInvitation.as_view()


class PendingReceivedInvitations(generic.ListView):
    template_name = 'invite/list.html'

    def get_queryset(self):
        return Invitation.objects.for_email(self.request.user.email).pending()

pending_received_invitations = PendingReceivedInvitations.as_view()


class PendingSentInvitations(generic.ListView):
    template_name = 'invite/list.html'

    def get_queryset(self):
        return self.request.user.sent_invitations.pending()

pending_sent_invitations = PendingSentInvitations.as_view()


class RedeemedOrExpiredInvitations(generic.ListView):
    template_name = 'invite/list.html'

    def get_queryset(self):
        return self.request.user.sent_invitations.not_pending()

redeemed_or_expired_invitations = RedeemedOrExpiredInvitations.as_view()
