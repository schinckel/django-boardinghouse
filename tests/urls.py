from __future__ import unicode_literals

from django.conf.urls import patterns, include, url
from django.db import connection
from django.http import HttpResponse
from django.shortcuts import render

from django.contrib import admin
admin.autodiscover()

from .models import AwareModel, NaiveModel

admin.site.register(AwareModel)
admin.site.register(NaiveModel)


def echo_schema(request):
    data = ""
    if request.GET:
        data = "\n" + "\n".join("%s=%s" % x for x in request.GET.items())
    return HttpResponse('%s' % request.session.get('schema') + data)


def change_schema_view(request):
    return render(request, 'boardinghouse/change_schema.html', {})


def aware_objects_view(request):
    obj = AwareModel.objects.all()[0]
    return HttpResponse(obj.name)


def sql_error(request):
    connection.cursor().execute('foo')


urlpatterns = patterns('',
    url(r'^$', echo_schema),
    url(r'^sql/error/$', sql_error),
    url(r'^change/$', change_schema_view),
    url(r'^aware/$', aware_objects_view),
    url(r'^admin/', include(admin.site.urls)),
) + patterns('django.contrib.auth.views',
    url(r'login/$', 'login', {'template_name': 'admin/login.html'}, name='login'),
    url(r'logout/$', 'logout_then_login', name='logout'),
)
