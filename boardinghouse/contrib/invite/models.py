import datetime

import django
from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _

# Can't import into the class namespace: we need to do it at the module.
if django.VERSION < (1,7):
    from model_utils.managers import PassThroughManager
else:
    pass

from boardinghouse.base import SharedSchemaModel

UserModel = getattr(settings, 'AUTH_USER_MODEL', 'auth.user')
INVITATION_EXPIRY = getattr(settings, 'INVITATION_EXPIRY', datetime.timedelta(7))

class InvitationQuerySet(models.query.QuerySet):
    def not_handled(self):
        return self.filter(declined_at=None, accepted_at=None)
    
    def pending(self):
        self.not_handled().filter(
            created_at__gte=datetime.datetime.utcnow()-INVITATION_EXPIRY
        )
    
    def expired(self):
        return self.not_handled().filter(
            created_at__lt=datetime.datetime.utcnow()-INVITATION_EXPIRY
        )
    
    def accepted(self):
        self.exclude(accepted_at=None)
    
    def declined(self):
        self.exclude(declined_at=None)

class Invitation(SharedSchemaModel):
    email = models.EmailField(verbose_name=_('Email address'))
    sender = models.ForeignKey(UserModel, related_name='sent_invitations')
    message = models.TextField()
    schema = models.ForeignKey('boardinghouse.schema')
    redemption_code = models.CharField(max_length=36, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    declined_at = models.DateTimeField(null=True, blank=True)
    
    if django.VERSION < (1,7):
        objects = PassThroughManager.for_queryset_class(InvitationQuerySet)()
    else:
        objects = InvitationQuerySet.as_manager()
    
    class Meta:
        ordering = ('created_at',)
        app_label = 'invite'
    
    def __unicode__(self):
        return 'Invitation to %s from %s to join %s' % (
            self.email, self.sender, self.schema.name
        )
    
    @property
    def redeemed(self):
        return self.accepted_at or self.declined_at
    
    @property
    def expired(self):
        return self.created_at > datetime.datetime.utcnow() - INVITATION_EXPIRY
    
    @property
    def redeemable(self):
        return not (self.expired or self.redeemed)
    