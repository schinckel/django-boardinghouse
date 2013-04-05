"""
Middleware to automatically set the schema (namespace).

if request.user.is_staff, then look for a ?__schema=XXX and set the schema to that.

Otherwise, set the schema to the one associated with the logged in user.


"""
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages
from django.utils.translation import ugettext as _
from django.shortcuts import redirect
from django.http import HttpResponse

from models import Schema


def activate_schema(available_schemata, session):
    """
    Activate the session's schema
    """
    if session.get('schema', None):
        try:
            available_schemata.get(pk=session['schema']).activate()
        except ObjectDoesNotExist:
            logging.warning(
                u'Unable to find Schema matching query: %s' % session['schema']
            )
            session.pop('schema')
        else:
            return True

class SchemaMiddleware:
    """
    Middleware to set the postgres schema for the current request.
    
    The schema that will be used is stored in the session. A lookup will
    occur (but this could easily be cached) on each request.
    
    To change schema, simply request a page with a querystring of:
    
        https://example.com/page/?__schema=<schema-name>
    
    The schema will be changed (or cleared, if this user cannot view 
    that schema), and the page will be re-loaded (if it was a GET).
    
    Alternatively, you may add a request header:
    
        X-Change-Schema: <schema-name>
    
    This will not cause a redirect to the same page without query string. It
    is the preferred method, because of that.
    
    There is also an injected url route:
    
        https://example.com/__change_schema__/<schema-name>/
    
    This is designed to be used from AJAX requests, as it returns a status
    code (and a short message) about the schema change request.
    
    """
    def process_request(self, request):
        if request.user.is_anonymous():
            return None
        if request.user.is_staff:
            available_schemata = Schema.objects
        elif request.user.schemata.exists():
            available_schemata = request.user.schemata
        
        if request.path.startswith('/__change_schema__/'):
            request.session['schema'] = request.path.split('/')[2]
            if not request.session['schema']:
                return HttpResponse('No schema selected: missing schema value', status=404)
            if activate_schema(available_schemata, request.session):
                return HttpResponse('Schema changed')
            return HttpResponse('Unable to change schema', status=403)
        elif request.GET.get('__schema', None):
            request.session['schema'] = request.GET['__schema']
            if request.method == "GET":
                data = request.GET.copy()
                data.pop('__schema')
                if data:
                    return redirect(request.path + '?' + data.urlencode())
                return redirect(request.path)
        elif 'HTTP_X_CHANGE_SCHEMA' in request.META:
            request.session['schema'] = request.META['HTTP_X_CHANGE_SCHEMA']
        
        activate_schema(available_schemata, request.session)

        
        
    def process_template_response(self, request, response):
        """
        Inject some context variables into the context for page
        rendering. This means we can get access to the schema
        information on each page, and use a schema switcher, as
        can be found in ``multi_schema/templates/change_schema.html``.
        
        It would be nice to prefix them with underscores, but then we
        would be unable to access them in the template.
        """
        
        if request.user.is_anonymous():
            return response
        
        if request.user.is_staff:
            available_schemata = Schema.objects.all()
        elif request.user.schemata.exists():
            available_schemata = request.user.schemata.all()
        else:
            # No schemata available for this user?
            available_schemata = Schema.objects.none()
        
        response.context_data['schemata'] = available_schemata
        
        if request.session.get('schema', None):
            response.context_data['selected_schema'] = request.session['schema']
        
        return response
