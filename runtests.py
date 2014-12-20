#!/usr/bin/env python

import os
import sys

from django.conf import settings
import django

try:
    from psycopg2cffi import compat
    compat.register()
except ImportError:
    pass

DEFAULT_SETTINGS = dict(
    INSTALLED_APPS=(
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'boardinghouse',
        'django.contrib.admin',
        'boardinghouse.contrib.invite',
        'tests',
        ),
    DATABASES={
        "default": {
            'ENGINE': 'boardinghouse.backends.postgres',
            'NAME': 'boardinghouse-{DB_NAME}'.format(**os.environ)
        }
    },
    ROOT_URLCONF='tests.urls',
    STATIC_URL='/static/',
    MIDDLEWARE_CLASSES=(
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
    ),
    PASSWORD_HASHERS = (
        'django.contrib.auth.hashers.MD5PasswordHasher',
    ),
)


def runtests():
    if not settings.configured:
        settings.configure(**DEFAULT_SETTINGS)

    django.setup()

    parent = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, parent)

    from django.test.runner import DiscoverRunner
    runner_class = DiscoverRunner
    test_args = ['tests']

    failures = runner_class(
        verbosity=1, interactive=True, failfast=False).run_tests(test_args)
    sys.exit(failures)


if __name__ == '__main__':
    runtests()
