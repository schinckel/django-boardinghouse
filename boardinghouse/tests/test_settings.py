from django.conf import settings
from django.test import TestCase


class TestSettings(TestCase):
    def test_SCHEMA_MODEL_is_set(self):
        settings.SCHEMA_MODEL