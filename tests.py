import os
import sys
import unittest
import doctest
import django

BASE_PATH = os.path.dirname(__file__)

def main():
    """
    Standalone django model test with a 'memory-only-django-installation'.
    You can play with a django model without a complete django app installation.
    http://www.djangosnippets.org/snippets/1044/
    """
    os.environ["DJANGO_SETTINGS_MODULE"] = "django.conf.global_settings"
    from django.conf import global_settings

    global_settings.INSTALLED_APPS = (
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.admin',
        'south',
        'multi_schema',
    )
    global_settings.DATABASES = {
        'default': {
            'ENGINE': 'multi_schema.backends.postgres',
            'NAME': os.environ['USER'],
        }
    } 
    global_settings.ROOT_URLCONF = 'multi_schema.tests.urls'
    
    global_settings.STATIC_URL = "/static/"
    global_settings.MEDIA_ROOT = os.path.join(BASE_PATH, 'static')
    global_settings.STATIC_ROOT = global_settings.MEDIA_ROOT
    
    global_settings.SECRET_KEY = '334ebe58-a77d-4321-9d01-a7d2cb8d3eea'
    global_settings.PASSWORD_HASHERS = (
        'django.contrib.auth.hashers.MD5PasswordHasher',
    )
    
    global_settings.TEST_RUNNER = 'django_coverage.coverage_runner.CoverageRunner'
    global_settings.COVERAGE_REPORT_HTML_OUTPUT_DIR = os.path.join(BASE_PATH, '.coverage')
    global_settings.COVERAGE_USE_STDOUT = True
    global_settings.COVERAGE_PATH_EXCLUDES = ['.hg', 'templates', 'tests', 'sql', '__pycache__']
    
    global_settings.SOUTH_DATABASE_ADAPTERS = {
        'default': 'multi_schema.backends.south_backend',
    }
    global_settings.MIDDLEWARE_CLASSES = global_settings.MIDDLEWARE_CLASSES + (
        'multi_schema.middleware.SchemaMiddleware',
    )
    global_settings.TEMPLATE_CONTEXT_PROCESSORS = global_settings.TEMPLATE_CONTEXT_PROCESSORS + (
        'multi_schema.context_processors.schemata',
    )
    from django.test.utils import get_runner
    test_runner = get_runner(global_settings)

    test_runner = test_runner()
    failures = test_runner.run_tests(['multi_schema'])
    
    sys.exit(failures)

if __name__ == '__main__':
    main()
