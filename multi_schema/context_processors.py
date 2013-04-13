from models import Schema

def schemata(request):
    if request.user.is_anonymous():
        return {}
    
    if request.user.is_staff or request.user.is_superuser:
        available_schemata = Schema.objects.all()
    elif request.user.schemata.exists():
        available_schemata = request.user.schemata.all()
    else:
        # No schemata available for this user?
        available_schemata = Schema.objects.none()
    
    return {
        'schemata': available_schemata,
        'selected_schema': request.session.get('schema', None)
    }