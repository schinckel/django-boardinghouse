from django.conf import settings
from django.test import TestCase
from django.core import checks

from boardinghouse import apps


class TestSettings(TestCase):
    def test_database_engine_not_valid(self):
        old_engine = settings.DATABASES['default']['ENGINE']
        settings.DATABASES['default']['ENGINE'] = 'foo.bar.baz'
        try:
            errors = apps.check_db_backend()
            self.assertEqual(1, len(errors))
            self.assertTrue(isinstance(errors[0], checks.Error))
            self.assertEqual('boardinghouse.E001', errors[0].id)
        finally:
            settings.DATABASES['default']['ENGINE'] = old_engine

    def test_session_middleware_missing(self):
        # Ensure our test MIDDLEWARE_CLASSES is valid, first.
        self.assertEqual([], apps.check_session_middleware_installed())
        middleware_classes = settings.MIDDLEWARE_CLASSES
        # Now empty it out, then test for check.Error
        settings.MIDDLEWARE_CLASSES = []
        try:
            errors = apps.check_session_middleware_installed()
            self.assertEqual(1, len(errors))
            self.assertTrue(isinstance(errors[0], checks.Error))
            self.assertEqual('boardinghouse.E002', errors[0].id)
        finally:
            settings.MIDDLEWARE_CLASSES = middleware_classes
