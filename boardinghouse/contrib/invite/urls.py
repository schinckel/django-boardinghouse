from django.conf.urls import patterns, url

urlpatterns = patterns('boardinghouse.contrib.invite.views', 
    url('^new/$', 'invite_person', name='new'),
    url('^view/(?P<redemption_code>[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})/$', 'view_invitation', name='view'),
)