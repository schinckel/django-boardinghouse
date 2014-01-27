
from schema import get_schema_model

def schemata(request):
    """
    A Django context_processor. This provides access to the
    logged-in user's visible schemata, and selected schema.
    
    This assumes you have an attribute ``schemata`` on request.user.
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