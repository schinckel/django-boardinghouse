try:
    from unittest.mock import Mock, call
except ImportError:
    from mock import Mock, call

from django.test import TestCase

from boardinghouse.models import Schema
from boardinghouse.schema import TemplateSchemaActivation
from boardinghouse.signals import session_requesting_schema_change, schema_aware_operation


class TestSignalsDirectly(TestCase):
    def test_template_activation_still_raises(self):
        with self.assertRaises(TemplateSchemaActivation):
            session_requesting_schema_change.send(sender=None, user=None, schema='__template__', session={})

    def test_schema_aware_operation(self):
        Schema.objects.mass_create('a', 'b', 'c')
        function = Mock()
        calls = [
            call('arg', kwarg=1),   # a
            call('arg', kwarg=1),   # b
            call('arg', kwarg=1),   # c
            call('arg', kwarg=1),   # __template__
        ]
        schema_aware_operation.send(sender=self,
                                    db_table='tests_awaremodel',
                                    function=function,
                                    args=['arg'],
                                    kwargs={'kwarg': 1})
        function.assert_has_calls(calls)
        self.assertEqual(4, function.call_count)
