from django.conf.urls import patterns, url

urlpatterns = patterns('boardinghouse.contrib.invite.views', 
    url('^new/$', 'invite_person', name='new'),
)