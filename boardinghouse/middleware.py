from __future__ import unicode_literals

import logging
import re

import django
from django.conf import settings
from django.contrib import messages
from django.db import ProgrammingError
from django.http import (
    HttpResponse, HttpResponseForbidden, HttpResponseRedirect,
)
from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _

from .schema import (
    Forbidden, TemplateSchemaActivation, activate_schema, deactivate_schema,
)
from .signals import session_requesting_schema_change, session_schema_changed

logger = logging.getLogger('boardinghouse.middleware')


def change_schema(request, schema):
    """
    Change the schema for the current request's session.

    Note this does not actually _activate_ the schema, it only stores
    the schema name in the current request's session.
    """
    session = request.session
    user = request.user

    # Allow clearing out the current schema.
    if not schema:
        session.pop('schema', None)
        return

    # Unauthenticated users may not select a schema.
    # Should this be selectable?
    if django.VERSION < (1, 10):
        if not user.is_authenticated():
            session.pop('schema', None)
            raise Forbidden
    elif not user.is_authenticated:
        session.pop('schema', None)
        raise Forbidden()

    # Make sure we have a schema name, not a model representing a schema.
    # This allows us to use a relation for User.visible_schemata, that contains
    # a relationship to schema objects, rather than a queryset of actual schema
    # objects.
    if hasattr(schema, 'schema'):
        schema = schema.schema

    # Don't allow anyone, even superusers, to select the template schema.
    if schema == settings.TEMPLATE_SCHEMA:
        raise TemplateSchemaActivation()

    # If the schema is already set to this name for this session, then
    # we can just exit early, potentially saving some db access.
    if schema == session.get('schema', None):
        return

    # Valid schema providers should listen for this signal, and do one of three
    # things: return an object that has a 'schema' attribute, return None, or
    # raise an exception. Returning an object with an attribute of 'schema' will
    # cause no further handlers to run. Returning None or False will cause the next
    # handler to attempt to find a valid schema, and raising an exception will
    # bubble up the call stack.
    for handler, response in session_requesting_schema_change.send(
        sender=request,
        schema=schema,
        user=user,
        session=session
    ):
        if response:
            if hasattr(response, 'schema'):
                session.update({
                    'schema': response.schema,
                    'schema_name': getattr(response, 'name', None),
                })
            if isinstance(response, dict) and 'schema' in response:
                session.update({
                    'schema': response['schema'],
                    'schema_name': response.get('name', None),
                })
            break
    else:
        # If no receivers stepped forwards to say they could handle it, that means
        # this user/session is not permitted to change to that schema.
        raise Forbidden()
    # Allow 3rd-party applications to listen for a change, and act upon
    # it accordingly.
    session_schema_changed.send(
        sender=request,
        schema=schema,
        user=user,
        session=session,
    )


class SchemaMiddleware(object):
    """
    Middleware to set the postgres schema for the current request's session.

    The schema that will be used is stored in the session. A lookup will
    occur (but this could easily be cached) on each request.

    There are three ways to change the schema as part of a request.

    1. Request a page with a querystring containg a ``__schema`` value::

        https://example.com/page/?__schema=<schema-name>

      The schema will be changed (or cleared, if this user cannot view
      that schema), and the page will be re-loaded (if it was a GET). This
      method of changing schema allows you to have a link that changes the
      current schema and then loads the data with the new schema active.

      It is used within the admin for having a link to data from an
      arbitrary schema in the ``LogEntry`` history.

      This type of schema change request should not be done with a POST
      request.

    2. Add a request header::

        X-Change-Schema: <schema-name>

      This will not cause a redirect to the same page without query string. It
      is the only way to do a schema change within a POST request, but could
      be used for any request type.

    3. Use a specific request::

        https://example.com/__change_schema__/<schema-name>/

      This is designed to be used from AJAX requests, or as part of
      an API call, as it returns a status code (and a short message)
      about the schema change request. If you were storing local data,
      and did one of these, you are probably going to have to invalidate
      much of that.

    You could also come up with other methods.

    """
    def __init__(self, get_response=None):
        # We should remove ourself if... when?
        self.get_response = get_response

    def __call__(self, request):
        try:
            return self.process_request(request) or self.get_response(request)
        except (TemplateSchemaActivation, ProgrammingError) as exception:
            return self.process_exception(request, exception)

    def process_request(self, request):
        FORBIDDEN = HttpResponseForbidden(_('You may not select that schema'))
        # Ways of changing the schema.
        # 1. URL /__change_schema__/<name>/
        # This will return a whole page.
        # We don't need to activate, that happens on the next request.
        if request.path.startswith('/__change_schema__/'):
            schema = request.path.split('/')[2]
            try:
                change_schema(request, schema)
            except Forbidden:
                return FORBIDDEN

            if 'schema' in request.session:
                response = _('Schema changed to %s') % request.session['schema']
            else:
                response = _('Schema deselected')

            return HttpResponse(response)

        # 2. GET querystring ...?__schema=<name>
        # This will change the query, and then redirect to the page
        # without the schema name included.
        elif request.GET.get('__schema', None) is not None:
            schema = request.GET['__schema']
            try:
                change_schema(request, schema)
            except Forbidden:
                return FORBIDDEN

            data = request.GET.copy()
            data.pop('__schema')

            if request.method == "GET":
                # redirect so we strip the schema out of the querystring.
                if data:
                    return redirect(request.path + '?' + data.urlencode())
                return redirect(request.path)

            # method == 'POST' or other
            request.GET = data

        # 3. Header "X-Change-Schema: <name>"
        elif 'HTTP_X_CHANGE_SCHEMA' in request.META:
            schema = request.META['HTTP_X_CHANGE_SCHEMA']
            try:
                change_schema(request, schema)
            except Forbidden:
                return FORBIDDEN

        elif 'schema' not in request.session and len(request.user.visible_schemata) == 1:
            change_schema(request, request.user.visible_schemata[0].schema)

        if 'schema' in request.session:
            activate_schema(request.session['schema'])
        else:
            deactivate_schema()

    def process_exception(self, request, exception):
        """
        In the case a request returned a DatabaseError, and there was no
        schema set on ``request.session``, then look and see if the error
        that was provided by the database may indicate that we should have
        been looking inside a schema.

        In the case we had a :class:`TemplateSchemaActivation` exception,
        then we want to remove that key from the session.
        """
        if isinstance(exception, ProgrammingError) and not request.session.get('schema'):
            if re.search('relation ".*" does not exist', exception.args[0]):
                # Should we return an error, or redirect? When should we
                # do one or the other? For an API, we would want an error
                # but for a regular user, a redirect may be better.
                if request.is_ajax():
                    return HttpResponse(
                        _('You must select a schema to access that resource'),
                        status=400
                    )
                # Can we see if there is already a pending message for this
                # request that has the same content as us?
                messages.error(request,
                    _("You must select a schema to access that resource"),
                    fail_silently=True
                )
                return HttpResponseRedirect('..')
        # I'm not sure we ever really hit this one, but it's worth keeping
        # here just in case we've missed something. I guess it could occur
        # if a view manually attempted to activate the template schema.
        if isinstance(exception, TemplateSchemaActivation):
            request.session.pop('schema', None)
            return HttpResponseForbidden(_('You may not select that schema'))

        raise exception
