from django.test import TestCase

from ..models import Schema
from .models import AwareModel, NaiveModel


class TestObjectEquality(TestCase):
    def test_objects_from_different_schema_differ(self):
        first = Schema.objects.create(name='first', schema='first')
        second = Schema.objects.create(name='second', schema='second')
        
        first.activate()
        object_1 = AwareModel.objects.create(name="foo")
        
        second.activate()
        object_2 = AwareModel.objects.create(name="foo")
        
        self.assertEqual(object_1.pk, object_2.pk)
        self.assertNotEqual(object_1, object_2, "Objects with the same id from different schemata should not be equal.")
    
    def test_objects_from_same_schema_equal(self):
        first = Schema.objects.create(name='first', schema='first')
        second = Schema.objects.create(name='second', schema='second')
        
        first.activate()
        object_1 = AwareModel.objects.create(name="foo")
        
        second.activate()
        object_2 = AwareModel.objects.create(name="foo")
        object_3 = AwareModel.objects.get(name="foo")
        
        self.assertEqual(object_2, object_3)
    
    def test_compare_aware_and_naive_objects(self):
        Schema.objects.create(name='schema', schema='schema').activate()
        aware = AwareModel.objects.create(name='foo')
        naive = NaiveModel.objects.create(name='foo')
        
        self.assertNotEqual(aware, naive)