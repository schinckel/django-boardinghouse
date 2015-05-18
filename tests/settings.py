import os

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'boardinghouse',
    'django.contrib.admin',
    # 'boardinghouse.contrib.invite',
    'tests',
]

DATABASES = {
    "default": {
        'ENGINE': 'boardinghouse.backends.postgres',
        'NAME': 'boardinghouse-{DB_NAME}'.format(**os.environ),
        'USER': os.environ.get('DB_USER', None),
        'TEST': {
            'SERIALIZE': False
        }
    }
}

ROOT_URLCONF = 'tests.urls'
STATIC_URL = '/static/'
MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)
PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.MD5PasswordHasher',
)
AUTH_USER_MODEL = 'auth.User'
SECRET_KEY = 'django-boardinghouse-sekret-keye'