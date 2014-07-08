import os
import sys
import unittest
import doctest
import django

BASE_PATH = os.path.dirname(__file__)

def runtests():
    """
    Standalone django model test with a 'memory-only-django-installation'.
    You can play with a django model without a complete django app installation.
    http://www.djangosnippets.org/snippets/1044/
    """
    os.environ["DJANGO_SETTINGS_MODULE"] = "django.conf.global_settings"
    from django.conf import global_settings

    global_settings.INSTALLED_APPS = (
        'boardinghouse',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.admin',
        'boardinghouse.contrib.invite',
    )
    global_settings.DATABASES = {
        'default': {
            'ENGINE': 'boardinghouse.backends.postgres',
            'NAME': os.environ['USER']
        }
    }
    global_settings.ROOT_URLCONF = 'boardinghouse.tests.urls'

    global_settings.STATIC_URL = "/static/"
    global_settings.MEDIA_ROOT = os.path.join(BASE_PATH, 'static')
    global_settings.STATIC_ROOT = global_settings.MEDIA_ROOT
    global_settings.TEMPLATE_DIRS = (
        os.path.join(BASE_PATH, 'boardinghouse', 'tests', 'templates'),
    )
    global_settings.SECRET_KEY = 'd1a1f7a0-7f88-4638-86d1-d71dc21634d7'
    global_settings.PASSWORD_HASHERS = (
        'django.contrib.auth.hashers.MD5PasswordHasher',
    )

    from django.test.utils import get_runner
    test_runner = get_runner(global_settings)

    django.setup()

    test_runner = test_runner()
    failures = test_runner.run_tests(['boardinghouse'])

    sys.exit(failures)

if __name__ == '__main__':
    runtests()
