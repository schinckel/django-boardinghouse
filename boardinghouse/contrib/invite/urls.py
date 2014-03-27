from django.conf.urls import patterns, url

urlpatterns = patterns('boardinghouse.contrib.invite.views', 
    url(r'^new/$', 'invite_person', name='new'),
    url(r'^view/(?P<redemption_code>[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12})/$', 'view_invitation', name='view'),
)