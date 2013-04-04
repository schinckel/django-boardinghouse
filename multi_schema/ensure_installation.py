from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

DB_ENGINE = 'multi_schema.backends.postgres'
SOUTH_DB_ADAPTER = 'multi_schema.backends.south_backend'
MULTI_SCHEMA_MIDDLEWARE = 'multi_schema.middleware.SchemaMiddleware'

for name in settings.DATABASES:
    current_db_engine = settings.DATABASES[name]['ENGINE']
    if current_db_engine != DB_ENGINE:
        raise ImproperlyConfigured('DATABASES["%s"][ENGINE] must be "%s", not "%s".' % (
            name, DB_ENGINE, current_db_engine
        ))
    
    if not hasattr(settings, 'SOUTH_DATABASE_ADAPTERS'):
        raise ImproperlyConfigured('You must set SOUTH_DATABASE_ADAPTERS for all DATABASES to "%s".' % SOUTH_DB_ADAPTER)
    
    current_south_adapter = settings.SOUTH_DATABASE_ADAPTERS.get(name, '<missing value>')
    if current_south_adapter != SOUTH_DB_ADAPTER:
        raise ImproperlyConfigured('SOUTH_DATABASE_ADAPTERS["%s"] must be "%s", not "%s".' % (
            name, SOUTH_DB_ADAPTER, current_south_adapter
        ))

if MULTI_SCHEMA_MIDDLEWARE not in settings.MIDDLEWARE_CLASSES:
    raise ImproperlyConfigured('You must have "%s" in your MIDDLEWARE_CLASSES.' % MULTI_SCHEMA_MIDDLEWARE)

if 'south' in settings.INSTALLED_APPS:
    if settings.INSTALLED_APPS.index('south') > settings.INSTALLED_APPS.index('multi_schema'):
        raise ImproperlyConfigured('You must have "south" in INSTALLED_APPS before "multi_schema".')