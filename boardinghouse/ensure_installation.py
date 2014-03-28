"""
This module ensures that all of the required parts of 
django-boardinghouse are correctly installed. It does
this in a rather hidden way: it injects the objects
that it thinks should be installed into the settings.

"""
import django
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

DB_ENGINES = ['boardinghouse.backends.postgres']
BOARDINGHOUSE_MIDDLEWARE = 'boardinghouse.middleware.SchemaChangeMiddleware'
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
    settings.MIDDLEWARE_CLASSES += (BOARDINGHOUSE_MIDDLEWARE, 'boardinghouse.middleware.SchemaActivationMiddleware')
# Should it be at the top? Is there anything it must be before?
# Anything it needs to be after? - authentication?

# We currently install this automatically, but it only makes sense to 
# install it if <user-model>.schemata exists. Perhaps we should supply
# several, and work out which one to install?
if BOARDINGHOUSE_CONTEXT_PROCESSOR not in settings.TEMPLATE_CONTEXT_PROCESSORS:
    settings.TEMPLATE_CONTEXT_PROCESSORS += (BOARDINGHOUSE_CONTEXT_PROCESSOR,)

if 'south' in settings.INSTALLED_APPS:
    # I'm not convinced this is the right place to do this.
    from south.models import MigrationHistory
    MigrationHistory._is_shared_model = True
    if settings.INSTALLED_APPS.index('south') > settings.INSTALLED_APPS.index('boardinghouse'):
        raise ImproperlyConfigured('You must have "south" in INSTALLED_APPS before "boardinghouse".')

if 'django.contrib.admin' in settings.INSTALLED_APPS:
    if settings.INSTALLED_APPS.index('django.contrib.admin') < settings.INSTALLED_APPS.index('boardinghouse'):
        raise ImproperlyConfigured('You must have "django.contrib.admin" in INSTALLED_APPS after "boardinghouse".')

# We need the user model to have an attribute 'schemata', which is a
# relationship to Schema. However, this is hard to test, as when we have
# test data, we don't add that until after.

# django-devserver causes infinite recursion on django < 1.7
# when django-boardinghouse is installed.
if django.VERSION < (1,7):
    if 'devserver' in settings.INSTALLED_APPS:
        raise ImproperlyConfigured('django-devserver is incompatible with django-boardinghouse when running under django < 1.7')

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