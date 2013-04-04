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

if 'django.contrib.admin' in settings.INSTALLED_APPS:
    # Patch LogEntry to store reference to Schema if applicable.
    # We will assume that the LogEntry table does not exist...
    from django.contrib.admin.models import LogEntry
    from django.db import models
    from django.dispatch import receiver
    
    LogEntry.add_to_class(
        'object_schema', 
        models.ForeignKey('multi_schema.Schema', blank=True, null=True)
    )
    
    # Now, when we have an object that gets saved in the admin, we
    # want to store the schema in the log, ...
    @receiver(models.signals.pre_save, sender=LogEntry)
    def update_object_schema(sender, instance, **kwargs):
        obj = instance.get_edited_object()
        if obj._is_schema_aware:
            from schema import get_schema
            instance.object_schema = get_schema()
            
    
    # So we can add that bit to the url, and have links in the admin
    # that will automatically change the schema for us.
    get_admin_url = LogEntry.get_admin_url
    
    def new_get_admin_url(self):
        if self.object_schema_id:
            return get_admin_url(self) + '?__schema=%s' % self.object_schema_id
        
        return get_admin_url(self)
    
    LogEntry.get_admin_url = new_get_admin_url