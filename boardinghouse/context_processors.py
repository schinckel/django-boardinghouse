
from schema import get_schema_model

def schemata(request):
    """
    A Django context_processor that provides access to the
    logged-in user's visible schemata, and selected schema.
    """
    if request.user.is_anonymous():
        return {}
    
    if request.user.is_staff or request.user.is_superuser:
        available_schemata = get_schema_model().objects.all()
    else:
        available_schemata = request.user.schemata.all()
    
    return {
        'schemata': available_schemata,
        'selected_schema': request.session.get('schema', None)
    }
