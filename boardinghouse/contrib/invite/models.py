import datetime

from django.conf import settings
from django.db import models

UserModel = getattr(settings, 'AUTH_USER_MODEL', 'auth.user')
INVITATION_EXPIRY = getattr(settings, 'INVITATION_EXPIRY', datetime.timedelta(7))

class InvitationQuerySet(models.query.QuerySet):
    def not_handled(self):
        return self.filter(declined_at=None, accepted_at=None)
    
    def pending(self):
        self.not_handled().filter(
            created_at__gte=datetime.datetime.now()-INVITATION_EXPIRY
        )
    
    def expired(self):
        return self.not_handled().filter(
            created_at__lt=datetime.datetime.now()-INVITATION_EXPIRY
        )
    
    def accepted(self):
        self.exclude(accepted_at=None)
    
    def declined(self):
        self.exclude(declined_at=None)

class Invitation(models.Model):
    email = models.EmailField()
    sender = models.ForeignKey(UserModel, related_name='sent_invitations')
    message = models.TextField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    declined_at = models.DateTimeField(null=True, blank=True)
    
    objects = InvitationQuerySet.as_manager()
    
    class Meta:
        order_by = ('created_at',)
    