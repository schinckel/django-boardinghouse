"""
Middleware to automatically set the schema (namespace).

if request.user.is_superuser, then look for a ?schema=XXX and set the schema to that.

Otherwise, set the schema to the one associated with the logged in user.


"""
from models import Schema

class SchemaMiddleware:
    def process_request(self, request):
        if request.user.is_anonymous():
            return None
        if request.user.is_superuser and '__schema' in request.GET:
            request.session['schema'] = request.GET['__schema']
        if request.user.is_superuser and 'schema' in request.session:
            Schema.objects.get(pk=request.session['schema']).activate()
        else:
            request.user.schema.schema.activate()
    
    def process_response(self, request):
        pass