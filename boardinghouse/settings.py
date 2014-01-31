SHARED_MODELS = [
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
"""
Models that should be in the public/shared schema, 
rather than in each tenant's schema.
"""