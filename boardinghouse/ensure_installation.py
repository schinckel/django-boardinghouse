"""
This module ensures that all of the required parts of 
django-boardinghouse are correctly installed. It does
this in a rather hidden way: it injects the objects
that it thinks should be installed into the settings.

"""
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

DB_ENGINES = ['boardinghouse.backends.postgres']
BOARDINGHOUSE_MIDDLEWARE = 'boardinghouse.middleware.SchemaMiddleware'
BOARDINGHOUSE_CONTEXT_PROCESSOR = 'boardinghouse.context_processors.schemata'

for name in settings.DATABASES:
    current_db_engine = settings.DATABASES[name]['ENGINE']
    if current_db_engine not in DB_ENGINES:
        raise ImproperlyConfigured(
            'DATABASES["%s"]["ENGINE"]: %s is not a supported engine. '
            'Supported engines are: %s' % (
                name, current_db_engine, DB_ENGINES
        ))

if BOARDINGHOUSE_MIDDLEWARE not in settings.MIDDLEWARE_CLASSES:
    settings.MIDDLEWARE_CLASSES += (BOARDINGHOUSE_MIDDLEWARE,)
# Should it be at the top? Is there anything it must be before?

if BOARDINGHOUSE_CONTEXT_PROCESSOR not in settings.TEMPLATE_CONTEXT_PROCESSORS:
    settings.TEMPLATE_CONTEXT_PROCESSORS += (BOARDINGHOUSE_CONTEXT_PROCESSOR,)

if 'south' in settings.INSTALLED_APPS:
    if settings.INSTALLED_APPS.index('south') > settings.INSTALLED_APPS.index('boardinghouse'):
        raise ImproperlyConfigured('You must have "south" in INSTALLED_APPS before "boardinghouse".')

if 'django.contrib.admin' in settings.INSTALLED_APPS:
    if settings.INSTALLED_APPS.index('django.contrib.admin') < settings.INSTALLED_APPS.index('boardinghouse'):
        raise ImproperlyConfigured('You must have "django.contrib.admin" in INSTALLED_APPS after "boardinghouse".')
    
    # Patch LogEntry to store reference to Schema if applicable.
    # We will assume that the LogEntry table does not exist.
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
            
    
    # ...so we can add that bit to the url, and have links in the admin
    # that will automatically change the schema for us.
    get_admin_url = LogEntry.get_admin_url
    
    def new_get_admin_url(self):
        if self.object_schema:
            return get_admin_url(self) + '?__schema=%s' % self.object_schema
        
        return get_admin_url(self)
    
    LogEntry.get_admin_url = new_get_admin_url

# We need the user model to have an attribute 'schemata', which is a
# relationship to Schema. However, this is hard to test, as when we have
# test data, we don't add that until after.


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