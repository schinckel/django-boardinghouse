"""
Middleware to automatically set the schema (namespace).

if request.user.is_staff, then look for a ?__schema=XXX and set the schema to that.

Otherwise, set the schema to the one associated with the logged in user.


"""

import logging
import re

from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.db import DatabaseError, transaction
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _

from .models import Schema, template_schema
from .schema import TemplateSchemaActivation

logger = logging.getLogger('boardinghouse')

def activate_schema(available_schemata, session):
    """
    Activate the session's schema.
    
    If the session's schema is set to __template__, then we will
    raise a :class:`TemplateSchemaActivation` exception.
    """
    if available_schemata.count() == 1:
        schema = available_schemata.get()
        session['schema'] = schema.schema
        schema.activate()
        return True
    
    if session.get('schema', None):
        if session['schema'] == '__template__':
            session.pop('schema', None)
            raise TemplateSchemaActivation()
        try:
            available_schemata.get(pk=session['schema']).activate()
        except ObjectDoesNotExist:
            logger.warning(
                _(u'Unable to find Schema matching query: %s') % session['schema']
            )
            session.pop('schema')

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
    
    This is designed to be used from AJAX requests, or as part of
    an API call, as it returns a status code (and a short message) 
    about the schema change request.
    
    """
    def process_request(self, request):
        template_schema.deactivate()
        available_schemata = Schema.objects.none()
        if request.user.is_anonymous():
            request.session['schema'] = None
            return None
        if request.user.is_staff or request.user.is_superuser:
            available_schemata = Schema.objects
        else:
            # What about if there is no attribute schemata on request.user?
            available_schemata = request.user.schemata
        
        # Ways of changing the schema.
        # 1. URL /__change_schema__/<name>/
        # This will return a whole page.
        if request.path.startswith('/__change_schema__/'):
            request.session['schema'] = request.path.split('/')[2]
            try:
                activate_schema(available_schemata, request.session)
            except TemplateSchemaActivation:
                return HttpResponseForbidden(_('You may not select that schema'))
            
            if request.session.get('schema'):
                response = _('Schema changed to %s') % request.session['schema']
            else:
                response = _("No schema found: schema deselected.")
            return HttpResponse(response)
        # 2. GET querystring ...?__schema=<name>
        # This will change the query, and then redirect to the page
        # without the schema name included.
        elif request.GET.get('__schema', None) is not None:
            request.session['schema'] = request.GET['__schema']
            if request.method == "GET":
                data = request.GET.copy()
                data.pop('__schema')
                if data:
                    return redirect(request.path + '?' + data.urlencode())
                return redirect(request.path)
        # 3. Header "X-Change-Schema: <name>"
        elif 'HTTP_X_CHANGE_SCHEMA' in request.META:
            request.session['schema'] = request.META['HTTP_X_CHANGE_SCHEMA']
        
        try:
            activate_schema(available_schemata, request.session)
        except TemplateSchemaActivation:
            return HttpResponseForbidden(_('You may not select that schema'))


    def process_exception(self, request, exception):
        """
        In the case a request returned a DatabaseError, and there was no
        schema set on ``request.session``, then look and see if the error
        that was provided by the database may indicate that we should have
        been looking inside a schema.
        
        In the case we had a :class:`TemplateSchemaActivation` exception,
        then we want to remove that key from the session.
        """
        if isinstance(exception, DatabaseError) and not request.session.get('schema'):
            if re.search('relation ".*" does not exist', exception.message):
                # TODO: make this styleable?
                transaction.rollback()
                return HttpResponse(_("You must select a schema to access this resource"), status=449)
        if isinstance(exception, TemplateSchemaActivation):
            request.session.pop('schema', None)
            return HttpResponseForbidden(_('You may not select that schema'))