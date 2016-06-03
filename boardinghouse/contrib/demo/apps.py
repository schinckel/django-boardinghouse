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
    from django.conf import settings

    if not settings.BOARDINGHOUSE_DEMO_PREFIX.startswith('_'):
        return [Error('BOARDINGHOUSE_DEMO_PREFIX must start with an underscore',
                      id='boardinghouse.contrib.demo.E001')]

    return []


@register('settings')
def check_demo_expiry_is_timedelta(app_configs=None, **kwargs):
    from django.conf import settings

    if not isinstance(settings.BOARDINGHOUSE_DEMO_PERIOD, datetime.timedelta):
        return [Error('BOARDINGHOUSE_DEMO_PERIOD must be a datetime.timedelta() instance',
                      id='boardinghouse.contrib.demo.E002')]

    return []
