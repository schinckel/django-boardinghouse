from django.test import TestCase

from boardinghouse.models import Schema


class TestSchemaQuerysetMethods(TestCase):
    def test_active(self):
        Schema.objects.mass_create('a', 'b', 'c')
        self.assertEquals(
            set(['a', 'b', 'c']),
            set(Schema.objects.active().values_list('schema', flat=True))
        )

        Schema.objects.filter(schema='a').update(is_active=False)
        self.assertEquals(
            set(['b', 'c']),
            set(Schema.objects.active().values_list('schema', flat=True))
        )


    def test_inactive(self):
        Schema.objects.mass_create('a', 'b', 'c')
        self.assertEquals(
            set([]),
            set(Schema.objects.inactive().values_list('schema', flat=True))
        )

        Schema.objects.filter(schema='a').update(is_active=False)
        self.assertEquals(
            set(['a']),
            set(Schema.objects.inactive().values_list('schema', flat=True))
        )
