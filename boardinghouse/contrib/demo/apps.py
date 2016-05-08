from django.apps import AppConfig


class BoardingHouseDemoConfig(AppConfig):
    name = 'boardinghouse.contrib.demo'

    def ready(self):
        # Make sure our required setting exists.
        from django.conf import settings
        if not hasattr(settings, 'BOARDINGHOUSE_DEMO_PREFIX'):
            settings.BOARDINGHOUSE_DEMO_PREFIX = '__demo_'

        from boardinghouse.contrib.demo import receivers  # NOQA
