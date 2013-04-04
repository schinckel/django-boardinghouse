"""
Middleware to automatically set the schema (namespace).

if request.user.is_staff, then look for a ?__schema=XXX and set the schema to that.

Otherwise, set the schema to the one associated with the logged in user.


"""
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages
from django.utils.translation import ugettext as _

from models import Schema

def activate_schema(request, available_schemata):
    if '__schema' in request.GET:
        request.session['schema'] = request.GET['__schema']
    if 'schema' in request.session:
        try:
            available_schemata.get(pk=request.session['schema']).activate()
        except ObjectDoesNotExist:
            messages.add_message(request, messages.WARNING, 
                _(u'Unable to find Schema matching query: %s' % request.session['schema'])
            )
            request.session.pop('schema')
        else:
            return None

class SchemaMiddleware:
    def process_request(self, request):
        if request.user.is_anonymous():
            return None
        if request.user.is_staff:
            available_schemata = Schema.objects
        elif request.user.schemata.exists():
            available_schemata = request.user.schemata
            
        activate_schema(request, available_schemata)
        
    def process_template_response(self, request, response):
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
        
        if 'schema' in request.session:
            response.context_data['selected_schema'] = request.session['schema']
        
        return response
