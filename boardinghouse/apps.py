from __future__ import unicode_literals

from django.apps import AppConfig
from django.core.checks import register, Error, Warning

CONTEXT = 'boardinghouse.context_processors.schemata'
MIDDLEWARE = 'boardinghouse.middleware.SchemaMiddleware'
DB_ENGINES = ['boardinghouse.backends.postgres']


class BoardingHouseConfig(AppConfig):
    """
    Default AppConfig for django-boardinghouse.
    """
    name = 'boardinghouse'

    def ready(self):
        load_app_settings()
        monkey_patch_user()
        register_signals()


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
    from django.conf import settings

    for middleware in settings.MIDDLEWARE_CLASSES:
        if middleware.endswith('.SessionMiddleware'):
            return []

    return [Error(
        'It appears that no session middleware is installed.',
        hint="Add 'django.contrib.sessions.middleware.SessionMiddleware' to your MIDDLEWARE_CLASSES",
        id='boardinghouse.E002',
    )]


def load_app_settings():
    """
    Load up the app settings defaults.

    See :mod:`boardinghouse.settings`
    """
    from boardinghouse import settings as app_settings
    from django.conf import settings, global_settings

    for key in dir(app_settings):
        if key.isupper():
            value = getattr(app_settings, key)
            setattr(global_settings, key, value)
            if not hasattr(settings, key):
                setattr(settings, key, value)


@register('settings')
def check_middleware_installed(app_configs=None, **kwargs):
    "Ensure that _our_ middleware is installed."
    from django.conf import settings

    errors = []

    if MIDDLEWARE not in settings.MIDDLEWARE_CLASSES:
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


def monkey_patch_user():
    """
    Add a property to the defined user model that gives us the visible schemata.

    Add properties to :class:`django.contrib.auth.models.AnonymousUser` that
    return empty querysets for visible and all schemata.
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


def register_signals():
    from django.db import models
    from boardinghouse import signals
    from .schema import get_schema_model

    Schema = get_schema_model()

    # How do we identify that this schema should be created from a different
    # template? Where can we get that information?
    models.signals.post_save.connect(signals.create_schema,
                                     sender=Schema,
                                     weak=False,
                                     dispatch_uid='create-schema')

    models.signals.post_delete.connect(signals.drop_schema, sender=Schema, weak=False)

    models.signals.post_init.connect(signals.inject_schema_attribute, sender=None)

    models.signals.m2m_changed.connect(signals.invalidate_cache,
                                       sender=Schema.users.through)

    models.signals.post_save.connect(signals.invalidate_all_user_caches, sender=Schema, weak=False)

    models.signals.pre_migrate.connect(signals.invalidate_all_caches, weak=False)

    signals.schema_aware_operation.connect(signals.execute_on_all_schemata, weak=False)
    signals.schema_aware_operation.connect(signals.execute_on_template_schema, weak=False)
