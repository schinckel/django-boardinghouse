from __future__ import unicode_literals


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

    return {
        'schemata': request.user.visible_schemata,
        'schema_choices': request.user.visible_schemata.values_list('schema', 'name'),
        'selected_schema': request.session.get('schema', None),
    }
