from django.conf.urls import include, url

from boardinghouse.contrib.invite import views

urlpatterns = [
    url(r'^new/$', views.invite_person, name='new'),

    url(r'^(?P<redemption_code>[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12})/',
        include([
            url(r'^$', views.view_invitation, name='view'),
            url(r'^accept/$', views.accept_invitation, name='accept'),
            url(r'^confirm/$', views.confirm_invitation, name='confirm'),
            url(r'^decline/$', views.decline_invitation, name='decline'),
        ])
    ),

    url(r'^received/$', views.pending_received_invitations, name='received'),
    url(r'^sent/$', views.pending_sent_invitations, name='sent'),
    url(r'^processed/$', views.redeemed_or_expired_invitations, name='processed'),
]
