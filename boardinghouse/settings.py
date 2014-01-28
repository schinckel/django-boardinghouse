from django.conf import global_settings

global_settings.SHARED_MODELS = [
    'auth.user',
    'auth.permission',
    'auth.group',
    'sites.site',
    'sessions.session',
    'contenttypes.contenttype',
    'admin.logentry',
    'south.migrationhistory',
    'migrations.migration',
]

global_settings.SCHEMA_MODEL = 'boardinghouse.schema'