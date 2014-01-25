"""
Django settings for demo_project project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

import django

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'c^3@9lyia%1ckn*mbdtu$l%+w#-+=(1zdpmdq=@d@1fc88(ka3'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
) + (('south', ) if django.VERSION < 1.7 else ()) + (
    'boardinghouse',
    'django.contrib.admin',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'boardinghouse.test.urls'

WSGI_APPLICATION = 'boardinghouse.test.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'boardinghouse.backends.postgres',
        'NAME': os.environ['USER']
    }
}

SOUTH_DATABASE_ADAPTERS = {
    'default': 'boardinghouse.backends.south_backend',
    'boardinghouse.backends.postgres': 'boardinghouse.backends.south_backend',
}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'



TEMPLATE_DIRS = (
    os.path.join(BASE_DIR, 'templates'),
)

PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.MD5PasswordHasher',
)

COVERAGE_REPORT_HTML_OUTPUT_DIR = os.path.join(BASE_DIR, '.coverage')
COVERAGE_USE_STDOUT = True
COVERAGE_PATH_EXCLUDES = ['.hg', 'templates', 'tests', 'sql', '__pycache__']

# if os.environ.get('COVERAGE', None):
#     from django_coverage import coverage_runner
#     test_runner = coverage_runner.CoverageRunner
# else:
#     from django.test.utils import get_runner
#     test_runner = get_runner(global_settings)
