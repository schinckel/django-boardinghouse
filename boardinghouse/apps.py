from __future__ import unicode_literals

from django.apps import AppConfig
from django.core.checks import Error, Warning, register

CONTEXT = 'boardinghouse.context_processors.schemata'
MIDDLEWARE = 'boardinghouse.middleware.SchemaMiddleware'
DB_ENGINES = ['boardinghouse.backends.postgres']


class BoardingHouseConfig(AppConfig):
    """
    Default AppConfig for django-boardinghouse.
    """
    name = 'boardinghouse'

    def ready(self):
        # Make sure that all default settings have been applied (if not overwritten).
        from boardinghouse import settings as app_settings
        from django.conf import settings, global_settings
        for key in dir(app_settings):
            if key.isupper():
                value = getattr(app_settings, key)
                setattr(global_settings, key, value)
                if not hasattr(settings, key):
                    setattr(settings, key, value)

        # Make non-logged-in users unable to view any schemata.
        from django.contrib.auth import get_user_model, models
        from boardinghouse.schema import get_schema_model
        from boardinghouse.models import visible_schemata

        User = get_user_model()

        models.AnonymousUser.visible_schemata = get_schema_model().objects.none()

        if not hasattr(User, 'visible_schemata'):
            User.visible_schemata = property(visible_schemata)

        if hasattr(User, 'schemata'):
            models.AnonymousUser.schemata = get_schema_model().objects.none()

        from boardinghouse import receivers  # NOQA


@register('settings')
def check_db_backend(app_configs=None, **kwargs):
    "Ensure all database backends are using a backend that we work with."
    from django.conf import settings
    errors = []

    for name, data in settings.DATABASES.items():
        if data['ENGINE'] not in DB_ENGINES:
            errors.append(Error(
                'DATABASES[%s][ENGINE] of %s is not a known backend.' % (
                    name, data['ENGINE']
                ),
                hint="Try boardinghouse.backends.postgres",
                id='boardinghouse.E001',
            ))

    return errors


@register('settings')
def check_session_middleware_installed(app_configs=None, **kwargs):
    """Ensure that SessionMiddleware is installed.

    Without it, we would be unable to store which schema should
    be active for a given request.
    """
    import django
    from django.conf import settings

    if django.VERSION < (1, 10):
        for middleware in settings.MIDDLEWARE_CLASSES:
            if middleware.endswith('.SessionMiddleware'):
                return []

        return [Error(
            'It appears that no session middleware is installed.',
            hint="Add 'django.contrib.sessions.middleware.SessionMiddleware' to your MIDDLEWARE_CLASSES",
            id='boardinghouse.E002',
        )]

    for middleware in settings.MIDDLEWARE:
        if middleware.endswith('.SessionMiddleware'):
            return []

    return [Error(
        'It appears that no session middleware is installed.',
        hint="Add 'django.contrib.sessions.middleware.SessionMiddleware' to your MIDDLEWARE",
        id='boardinghouse.E002',
    )]


@register('settings')
def check_middleware_installed(app_configs=None, **kwargs):
    "Ensure that _our_ middleware is installed."
    import django
    from django.conf import settings

    if django.VERSION < (1, 10):
        MIDDLEWARE_CLASSES = settings.MIDDLEWARE_CLASSES
    else:
        MIDDLEWARE_CLASSES = settings.MIDDLEWARE

    errors = []

    if MIDDLEWARE not in MIDDLEWARE_CLASSES:
        errors.append(Error(
            'Missing required middleware',
            hint="Add '{}' to settings.MIDDLEWARE_CLASSES".format(MIDDLEWARE),
            id='boardinghouse.E003'
        ))

    return errors


@register('settings')
def check_context_processor_installed(app_configs=None, **kwargs):
    "Warn if our context processor is not installed."
    from django.conf import settings

    errors = []

    if hasattr(settings, 'TEMPLATES'):
        for i, engine in enumerate(settings.TEMPLATES):
            if CONTEXT not in engine.get('OPTIONS', {}).get('context_processors', []):
                errors.append(Warning(
                    'Missing boardinghouse context processor',
                    hint="Add '{1}' to settings.TEMPLATES[{0}]"
                         "['OPTIONS']['context_processors']".format(i, CONTEXT),
                    id='boardinghouse.W001'
                ))
    elif hasattr(settings, 'TEMPLATE_CONTEXT_PROCESSORS'):
        if CONTEXT not in settings.TEMPLATE_CONTEXT_PROCESSORS:
            errors.append(Warning(
                'Missing boardinghouse context processor',
                hint="Add '{}' to settings.TEMPLATE_CONTEXT_PROCESSORS".format(CONTEXT),
                id='boardinghouse.W001'
            ))
    else:
        errors.append(Warning(
            'Missing boardinghouse context processor (no TEMPLATES defined)',
            hint="Configure settings.TEMPLATES and add '{}'".format(CONTEXT),
            id='boardinghouse.W001',
        ))

    return errors


@register('settings')
def check_installed_before_admin(app_configs=None, **kwargs):
    """
    If `django.contrib.admin` is also installed, we must be installed before it.

    Is this even true anymore?
    """
    from django.conf import settings

    errors = []

    if 'django.contrib.admin' in settings.INSTALLED_APPS:
        admin = settings.INSTALLED_APPS.index('django.contrib.admin')
        local = settings.INSTALLED_APPS.index('boardinghouse')
        if admin < local:
            errors.append(Error(
                "boardinghouse must be installed prior to 'django.contrib.admin'",
                id='boardinghouse.E004',
            ))

    return errors
