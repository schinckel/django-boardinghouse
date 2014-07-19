from __future__ import unicode_literals

from .schema import get_schema_model


def schemata(request):
    """
    A Django context_processor that provides access to the
    logged-in user's visible schemata, and selected schema.

    Adds the following variables to the context:

        `schemata`: all available schemata this user has

        `selected_schema`: the currenly selected schema name

    """
    if request.user.is_anonymous():
        return {}

    if request.user.is_staff or request.user.is_superuser:
        available_schemata = get_schema_model().objects.all()
    else:
        available_schemata = request.user.visible_schemata

    return {
        'schemata': available_schemata,
        'selected_schema': request.session.get('schema', None)
    }
