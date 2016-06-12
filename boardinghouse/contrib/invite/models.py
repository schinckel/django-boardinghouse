import datetime
import uuid

from django.conf import settings
from django.db import models
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _

from boardinghouse.base import SharedSchemaModel

# Can't import into the class namespace: we need to do it at the module.


INVITATION_EXPIRY = getattr(settings, 'INVITATION_EXPIRY', datetime.timedelta(7))


class InvitationQuerySet(models.query.QuerySet):
    def not_handled(self):
        return self.filter(declined_at=None).filter(accepted_at=None)

    def pending(self):
        return self.not_handled().filter(
            created_at__gte=now() - INVITATION_EXPIRY
        )

    def not_pending(self):
        # Any invitations that have expired, have been accepted or declined.
        return self.exclude(pk__in=self.pending())

    def expired(self):
        return self.not_handled().filter(
            created_at__lt=now() - INVITATION_EXPIRY
        )

    def accepted(self):
        return self.exclude(accepted_at=None)

    def declined(self):
        return self.exclude(declined_at=None)

    def for_email(self, email):
        return self.filter(email=email)


class Invitation(SharedSchemaModel):
    email = models.EmailField(verbose_name=_('Email address'))
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='sent_invitations')
    message = models.TextField()
    schema = models.ForeignKey(settings.BOARDINGHOUSE_SCHEMA_MODEL, related_name='invitations')
    redemption_code = models.UUIDField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    # Can we ensure that at most one of these two is not null?
    accepted_at = models.DateTimeField(null=True, blank=True)
    declined_at = models.DateTimeField(null=True, blank=True)
    accepted_by = models.ForeignKey(settings.AUTH_USER_MODEL,
                                    related_name='accepted_invitations',
                                    null=True, blank=True)

    objects = InvitationQuerySet.as_manager()

    class Meta:
        ordering = ('created_at',)
        app_label = 'invite'

    def __unicode__(self):
        return '[{0!s}] Invitation to {1!s} from {2!s} to join {3!s}'.format(
            unicode(self.status), self.email, self.sender, self.schema.name
        )

    def save(self, *args, **kwargs):
        if not self.redeemed and not self.redemption_code:
            self.redemption_code = uuid.uuid4()
        return super(Invitation, self).save(*args, **kwargs)

    @property
    def redeemed(self):
        return self.accepted_at or self.declined_at

    @property
    def declined(self):
        return self.declined_at is not None

    @property
    def accepted(self):
        return self.accepted_at is not None

    @property
    def expired(self):
        return self.created_at < now() - INVITATION_EXPIRY

    @property
    def redeemable(self):
        return not (self.expired or self.redeemed)

    @property
    def status(self):
        if self.declined:
            return _('DECLINED')
        if self.accepted:
            return _('ACCEPTED')
        if self.expired:
            return _('EXPIRED')
        return _('PENDING')

    @property
    def expires_at(self):
        return self.created_at + INVITATION_EXPIRY
