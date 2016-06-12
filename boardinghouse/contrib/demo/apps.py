import datetime

from django.apps import AppConfig
from django.core.checks import Error, register


class BoardingHouseDemoConfig(AppConfig):
    name = 'boardinghouse.contrib.demo'

    def ready(self):
        # Make sure our required setting exists.
        from django.conf import settings

        if not hasattr(settings, 'BOARDINGHOUSE_DEMO_PREFIX'):
            settings.BOARDINGHOUSE_DEMO_PREFIX = '__demo_'

        if not hasattr(settings, 'BOARDINGHOUSE_DEMO_PERIOD'):
            settings.BOARDINGHOUSE_DEMO_PERIOD = datetime.timedelta(31)

        from boardinghouse.contrib.demo import receivers  # NOQA


@register('settings')
def check_demo_prefix_stats_with_underscore(app_configs=None, **kwargs):
    """Ensure that the prefix for demo schemata internal names starts with underscore.

    This is required because a leading underscore is the trigger that the indicated
    schema is not a "regular" schema, and should not be activated according to the
    normal rules.
    """
    from django.conf import settings

    if not settings.BOARDINGHOUSE_DEMO_PREFIX.startswith('_'):
        return [Error('BOARDINGHOUSE_DEMO_PREFIX must start with an underscore',
                      id='boardinghouse.contrib.demo.E001')]

    return []


@register('settings')
def check_demo_expiry_is_timedelta(app_configs=None, **kwargs):
    """
    BOARDINGHOUSE_DEMO_PERIOD should be a timedelta instance.
    """
    from django.conf import settings

    if not isinstance(settings.BOARDINGHOUSE_DEMO_PERIOD, datetime.timedelta):
        return [Error('BOARDINGHOUSE_DEMO_PERIOD must be a datetime.timedelta() instance',
                      id='boardinghouse.contrib.demo.E002')]

    return []


@register('settings')
def ensure_contrib_template_installed(app_configs=None, **kwargs):
    """
    `boardinghouse.contrib.template` must be installed.
    """
    from django.apps import apps

    if not apps.is_installed('boardinghouse.contrib.template'):
        return [Error('"boardinghouse.contrib.template" must be installed for "boardinghouse.contrib.demo"',
                      id='boardinghouse.contrib.demo.E003')]

    return []
