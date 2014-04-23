import datetime
import uuid

from django import forms
from django.utils.translation import ugettext_lazy as _

from boardinghouse.schema import get_schema

from .models import Invitation

ALREADY_REDEEMED = _('This invitation has already been redeemed.')
EXPIRED = _('This invitation has expired.')
ACCEPTED = _('This invitation has already been accepted.')
DECLINED = _('This invitation has already been declined.')

class InvitePersonForm(forms.ModelForm):
    """
    A form that can be used to create a new invitation for a person
    to a schema.
    
    This will only allow you to invite someone to the current schema.
    
    It will automatically generate a redemption code, that will be a
    part of the url the user needs to click on in order to accept or
    deny the invitation.
    
    The message will be emailed.
    """
    class Meta:
        model = Invitation
        fields = ('email', 'message',)
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(InvitePersonForm, self).__init__(*args, **kwargs)
        
    def save(self, *args, **kwargs):
        self.instance.schema = get_schema()
        self.instance.redemption_code = uuid.uuid4()
        self.instance.sender = self.user
        # TODO: email the user.
        return super(InvitePersonForm, self).save(*args, **kwargs)

class AcceptForm(forms.ModelForm):
    """
    A form that can be used to accept an invitation to a schema.
    """
        
    class Meta:
        model = Invitation
        fields = ()
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(AcceptForm, self).__init__(*args, **kwargs)
    
    def clean(self):
        if self.instance.expired:
            raise forms.ValidationError(EXPIRED)
        if self.instance.redeemed:
            raise forms.ValidationError(ACCEPTED)
        if self.instance.declined:
            raise forms.ValidationError(DECLINED)
        return self.cleaned_data
    
    def save(self, *args, **kwargs):
        self.user.schemata.add(self.instance.schema)
        self.instance.accepted_at = datetime.datetime.utcnow()
        return super(AcceptForm, self).save(*args, **kwargs)

class DeclineForm(forms.ModelForm):
    
    class Meta:
        model = Invitation
        fields = ()
    
    def clean(self):
        # In this case, we just want to tell the user this object
        # has been accepted, since they attempted to decline it.
        if self.instance.accepted:
            raise forms.ValidationError(ACCEPTED)
        return {}
    
    def save(self, *args, **kwargs):
        self.instance.declined_at = datetime.datetime.utcnow()
        return super(DeclineForm, self).save(*args, **kwargs)