import django
from django.conf.urls import url

from .views import CreateDemo, DeleteDemo, ResetDemo

urlpatterns = [
    url(r'^create/$', CreateDemo.as_view(), name='create'),
    url(r'^delete/$', DeleteDemo.as_view(), name='delete'),
    url(r'^reset/$', ResetDemo.as_view(), name='reset'),
]

if django.VERSION < (1, 9):
    urlpatterns = (urlpatterns, 'demo', 'demo')
else:
    urlpatterns = (urlpatterns, 'demo')
