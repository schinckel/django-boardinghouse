from django.conf.urls import patterns, url

CODE = '(?P<redemption_code>[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12})'

urlpatterns = patterns('boardinghouse.contrib.invite.views', 
    url(r'^new/$', 'invite_person', name='new'),
    url(r'^%s/$' % CODE, 'view_invitation', name='view'),
    url(r'^%s/accept/$' % CODE, 'accept_invitation', name='accept'),
    url(r'^%s/confirm/$' % CODE, 'confirm_invitation', name='confirm'),
    url(r'^%s/decline/$' % CODE, 'decline_invitation', name='decline'),
)