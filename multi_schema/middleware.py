"""
Middleware to automatically set the schema (namespace).

if request.user.is_superuser, then look for a ?schema=XXX and set the schema to that.

Otherwise, set the schema to the one associated with the logged in user.


"""
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages
from django.utils.translation import ugettext as _

from models import Schema

class SchemaMiddleware:
    def process_request(self, request):
        if request.user.is_anonymous():
            return None
        if request.user.is_superuser:
            if '__schema' in request.GET:
                request.session['schema'] = request.GET['__schema']
            if 'schema' in request.session:
                try:
                    Schema.objects.get(pk=request.session['schema']).activate()
                except ObjectDoesNotExist:
                    # TODO Figure out how to not have the duplicate messages.
                    messages.add_message(request, messages.WARNING, 
                        _(u'Unable to find Schema matching query: %s' % request.session['schema'])
                    )
                else:
                    return None
        try:
            request.user.schema.schema.activate()
        except ObjectDoesNotExist:
            # If we require a schema, what should we do here? Logging it is fine, but how do we
            # know we need one for this request?
            pass
            
    
    def process_template_response(self, request, response):
        if request.user.is_superuser:
            response.context_data['schemata'] = Schema.objects.all()
            if 'schema' in request.session:
                response.context_data['selected_schema'] = request.session['schema']
            else:
                response.context_data['selected_schema'] = request.user.schema.schema_id
        return response
