"""
Middleware to automatically set the schema (namespace).

if request.user.is_superuser, then look for a ?schema=XXX and set the schema to that.

Otherwise, set the schema to the one associated with the logged in user.


"""
from django.core.exceptions import ObjectDoesNotExist

from models import Schema

class SchemaMiddleware:
    def process_request(self, request):
        if request.user.is_anonymous():
            return None
        if request.user.is_superuser:
            if '__schema' in request.GET:
                request.session['schema'] = request.GET['__schema']
            if 'schema' in request.session:
                Schema.objects.get(pk=request.session['schema']).activate()
        else:
            try:
                request.user.schema.schema.activate()
            except ObjectDoesNotExist:
                pass
            
    
    def process_template_response(self, request, response):
        if request.user.is_superuser:
            response.context_data['schemata'] = Schema.objects.all()
            response.context_data['selected_schema'] = request.session['schema']
        return response