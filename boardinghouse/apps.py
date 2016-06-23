from __future__ import unicode_literals

from django.apps import AppConfig
from django.core.checks import Error, Warning, register

CONTEXT = 'boardinghouse.context_processors.schemata'
MIDDLEWARE = 'boardinghouse.middleware.SchemaMiddleware'
DB_ENGINES = ['boardinghouse.backends.postgres']


class BoardingHouseConfig(AppConfig):
    """
    Default AppConfig for django-boardinghouse.

    This class ensures that all settings is `boardinghouse.settings` are present
    in the settings for the project. Defaults are pulled from that module.

    There are also a couple of monkey-patches that are applied: for instance,
    :class:`AnonymousUser` gets `visible_schemata` and `schemata` attributes,
    and the installed `User` model gets a `visible_schemata` if one is not present.

    Some extra models are added to the private models list (which needs to happen
    here because it relies on `django.contrib.auth` being installed)
    """
    name = 'boardinghouse'
    _ready_has_run = False

    def ready(self):
        if self._ready_has_run:
            return

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

        # Make sure User <--> Group and User <--> Permission are per-schema.
        # If this is not desired, then it needs to be overriden.
        settings.PRIVATE_MODELS.extend([
            '{m.app_label}.{m.model_name}'.format(m=User.groups.through._meta).lower(),
            '{m.app_label}.{m.model_name}'.format(m=User.user_permissions.through._meta).lower()
        ])

        from boardinghouse import receivers  # NOQA

        self._ready_has_run = True


@register('settings')
def check_db_backend(app_configs=None, **kwargs):
    "Ensure all database backends are using a backend that we work with."
    from django.conf import settings
    errors = []

    for name, data in settings.DATABASES.items():
        if data['ENGINE'] not in DB_ENGINES:
            errors.append(Error(
                'DATABASES[{0!s}][ENGINE] of {1!s} is not a known backend.'.format(
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

    if getattr(settings, 'MIDDLEWARE', None):
        for middleware in settings.MIDDLEWARE:
            if middleware.endswith('.SessionMiddleware'):
                return []

        return [Error(
            'It appears that no session middleware is installed.',
            hint="Add 'django.contrib.sessions.middleware.SessionMiddleware' to your MIDDLEWARE",
            id='boardinghouse.E002',
        )]
    elif hasattr(settings, 'MIDDLEWARE_CLASSES'):
        for middleware in settings.MIDDLEWARE_CLASSES:
            if middleware.endswith('.SessionMiddleware'):
                return []

        return [Error(
            'It appears that no session middleware is installed.',
            hint="Add 'django.contrib.sessions.middleware.SessionMiddleware' to your MIDDLEWARE_CLASSES",
            id='boardinghouse.E002',
        )]


@register('settings')
def check_middleware_installed(app_configs=None, **kwargs):
    "Ensure that _our_ middleware is installed."
    from django.conf import settings

    if getattr(settings, 'MIDDLEWARE', None):
        MIDDLEWARE_CLASSES = settings.MIDDLEWARE
    else:
        MIDDLEWARE_CLASSES = settings.MIDDLEWARE_CLASSES

    errors = []

    if MIDDLEWARE not in MIDDLEWARE_CLASSES:
        errors.append(Error(
            'Missing required middleware',
            hint="Add '{0}' to settings.MIDDLEWARE_CLASSES".format(MIDDLEWARE),
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
            # We only check for the context processor if using the default django backend.
            if engine['BACKEND'] != 'django.template.backends.django.DjangoTemplates':
                continue
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
                hint="Add '{0}' to settings.TEMPLATE_CONTEXT_PROCESSORS".format(CONTEXT),
                id='boardinghouse.W001'
            ))
    else:
        errors.append(Warning(
            'Missing boardinghouse context processor (no TEMPLATES defined)',
            hint="Configure settings.TEMPLATES and add '{0}'".format(CONTEXT),
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
