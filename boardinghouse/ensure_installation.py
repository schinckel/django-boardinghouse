from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

DB_ENGINE = 'boardinghouse.backends.postgres'
SOUTH_DB_ADAPTER = 'boardinghouse.backends.south_backend'
MULTI_SCHEMA_MIDDLEWARE = 'boardinghouse.middleware.SchemaMiddleware'
MULTI_SCHEMA_CONTEXT_PROCESSOR = 'boardinghouse.context_processors.schemata'

for name in settings.DATABASES:
    current_db_engine = settings.DATABASES[name]['ENGINE']
    if current_db_engine != DB_ENGINE:
        raise ImproperlyConfigured('DATABASES["%s"][ENGINE] must be "%s", not "%s".' % (
            name, DB_ENGINE, current_db_engine
        ))
    
    if 'south' in settings.INSTALLED_APPS:
        if not hasattr(settings, 'SOUTH_DATABASE_ADAPTERS'):
            raise ImproperlyConfigured('You must set SOUTH_DATABASE_ADAPTERS for all DATABASES to "%s".' % SOUTH_DB_ADAPTER)
    
        current_south_adapter = settings.SOUTH_DATABASE_ADAPTERS.get(name, '<missing value>')
        if current_south_adapter != SOUTH_DB_ADAPTER:
            raise ImproperlyConfigured('SOUTH_DATABASE_ADAPTERS["%s"] must be "%s", not "%s".' % (
                name, SOUTH_DB_ADAPTER, current_south_adapter
            ))

if MULTI_SCHEMA_MIDDLEWARE not in settings.MIDDLEWARE_CLASSES:
    raise ImproperlyConfigured('You must have "%s" in your MIDDLEWARE_CLASSES.' % MULTI_SCHEMA_MIDDLEWARE)
# Should it be at the top? Is there anything it must be before?

if MULTI_SCHEMA_CONTEXT_PROCESSOR not in settings.TEMPLATE_CONTEXT_PROCESSORS:
    # Change this to a warning? It is not _required_, just a simple way to get this data into the request context.
    raise ImproperlyConfigured('You must have "%s" in your TEMPLATE_CONTEXT_PROCESSORS.' % MULTI_SCHEMA_CONTEXT_PROCESSOR)

if 'south' in settings.INSTALLED_APPS:
    if settings.INSTALLED_APPS.index('south') > settings.INSTALLED_APPS.index('boardinghouse'):
        raise ImproperlyConfigured('You must have "south" in INSTALLED_APPS before "boardinghouse".')

if 'django.contrib.admin' in settings.INSTALLED_APPS:
    # Patch LogEntry to store reference to Schema if applicable.
    # We will assume that the LogEntry table does not exist...
    from django.contrib.admin.models import LogEntry
    from django.db import models
    from django.dispatch import receiver
    
    LogEntry.add_to_class(
        'object_schema', 
        models.CharField(max_length=36, blank=True, null=True)
    )
    
    # Now, when we have an object that gets saved in the admin, we
    # want to store the schema in the log, ...
    @receiver(models.signals.pre_save, sender=LogEntry)
    def update_object_schema(sender, instance, **kwargs):
        obj = instance.get_edited_object()
        if obj._is_schema_aware:
            from schema import get_schema
            instance.object_schema = get_schema().schema
            
    
    # So we can add that bit to the url, and have links in the admin
    # that will automatically change the schema for us.
    get_admin_url = LogEntry.get_admin_url
    
    def new_get_admin_url(self):
        if self.object_schema:
            return get_admin_url(self) + '?__schema=%s' % self.object_schema
        
        return get_admin_url(self)
    
    LogEntry.get_admin_url = new_get_admin_url

# # Hacks to get dumpdata/loaddata to work a bit better...
# from django.core.serializers.python import Serializer
# # django 1.5+
# if hasattr(Serializer, 'get_dump_object'):
#     _get_dump_object = Serializer.get_dump_object
# 
#     def get_dump_object(self, obj):
#         dump_object = _get_dump_object(self, obj)
#         if obj._is_schema_aware:
#             from schema import get_schema
#             dump_object['schema'] = get_schema().schema
#         return obj
#     
#     Serializer.get_dump_object = get_dump_object
# else: # django 1.4
#     _end_object = Serializer.end_object
#     def end_object(self, obj):
#         _end_object(self, obj)
#         if obj._is_schema_aware:
#             from schema import get_schema
#             self.objects[-1]['schema'] = get_schema().schema
#     Serializer.end_object = end_object