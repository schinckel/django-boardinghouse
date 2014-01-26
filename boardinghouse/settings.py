from django.conf import settings

SHARED_MODELS = [
    'auth.user',
    'auth.permission',
    'auth.group',
    'sites.site',
    'sessions.session',
]

SCHEMA_MODEL = [
    'boardinghouse.schema',
]

locals().update(getattr(settings, 'BOARDINGHOUSE', {}))