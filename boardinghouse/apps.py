from __future__ import unicode_literals

from django.apps import AppConfig
from django.core.checks import register, Error


class BoardingHouseConfig(AppConfig):
    name = 'boardinghouse'

    def ready(self):
        load_app_settings()
        inject_required_settings()
        monkey_patch_user()


DB_ENGINES = ['boardinghouse.backends.postgres']


@register('settings')
def check_db_backend(app_configs, **kwargs):
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
def check_session_middleware_installed(app_configs, **kwargs):
    from django.conf import settings
    for middleware in settings.MIDDLEWARE_CLASSES:
        if middleware.endswith('.SessionMiddleware'):
            return []

    return [Error(
        'It appears that no session middleware is installed.',
        hint="Add 'django.contrib.sessions.middleware.SessionMiddleware' to your MIDDLEWARE_CLASSES",
        id='boardinghouse.E002',
    )]


def monkey_patch_user():
    """
    We want to add a property to the defined user model that gives
    us the visible schemata: this will be cached.

    We also want to add properties to the AnonymousUser that
    always return an empty queryset.
    """
    from django.contrib.auth import get_user_model, models
    from .schema import get_schema_model
    from .models import visible_schemata
    Schema = get_schema_model()
    User = get_user_model()
    if not getattr(User, 'visible_schemata', None):
        User.visible_schemata = property(visible_schemata)

    models.AnonymousUser.schemata = Schema.objects.none()
    models.AnonymousUser.visible_schemata = Schema.objects.none()


def load_app_settings():
    from boardinghouse import settings as app_settings
    from django.conf import settings, global_settings

    for key in dir(app_settings):
        if key.isupper():
            value = getattr(app_settings, key)
            setattr(global_settings, key, value)
            if not hasattr(settings, key):
                setattr(settings, key, value)


def inject_required_settings():
    from django.conf import settings

    MIDDLEWARE = (
        'boardinghouse.middleware.SchemaChangeMiddleware',
        'boardinghouse.middleware.SchemaActivationMiddleware'
    )
    CONTEXT = 'boardinghouse.context_processors.schemata'

    if MIDDLEWARE[0] not in settings.MIDDLEWARE_CLASSES:
        settings.MIDDLEWARE_CLASSES += MIDDLEWARE

    if CONTEXT not in settings.TEMPLATE_CONTEXT_PROCESSORS:
        settings.TEMPLATE_CONTEXT_PROCESSORS += (CONTEXT,)
