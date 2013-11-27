from models import Schema

def schemata(request):
    if request.user.is_anonymous():
        return {}
    
    if request.user.is_staff or request.user.is_superuser:
        available_schemata = Schema.objects.all()
    else:
        available_schemata = request.user.schemata.all()
    
    return {
        'schemata': available_schemata,
        'selected_schema': request.session.get('schema', None)
    }