from django.conf import settings

SHARED_MODELS = [
    'auth.user',
    'auth.permission',
    'auth.group',
    'sites.site',
    'sessions.session',
    'contenttypes.contenttype',
    'admin.logentry',
    'south.migrationhistory'
]

SCHEMA_MODEL = [
    'boardinghouse.schema',
]

locals().update(getattr(settings, 'BOARDINGHOUSE', {}))