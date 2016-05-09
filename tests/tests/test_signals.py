from django.test import TestCase

from boardinghouse.schema import TemplateSchemaActivation
from boardinghouse.signals import session_requesting_schema_change


class TestSignalsDirectly(TestCase):
    def test_template_activation_still_raises(self):
        with self.assertRaises(TemplateSchemaActivation):
            session_requesting_schema_change.send(sender=None, user=None, schema='__template__', session={})
