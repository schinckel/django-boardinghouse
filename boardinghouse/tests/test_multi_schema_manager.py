from django.test import TestCase

from ..models import Schema
from .models import AwareModel, NaiveModel

class TestMultiSchemaManager(TestCase):
    def test_multi_schema_fetches_objects_correctly(self):
        Schema.objects.mass_create('a', 'b')
        
        a = Schema.objects.get(name='a')
        a.activate()
        AwareModel.objects.create(name='foo')
        AwareModel.objects.create(name='bar')
        AwareModel.objects.create(name='baz')
        
        b = Schema.objects.get(name='b')
        b.activate()
        AwareModel.objects.create(name='foo')
        AwareModel.objects.create(name='bar')
        AwareModel.objects.create(name='baz')
        
        b.deactivate()
        
        objects = list(AwareModel.objects.from_schemata(a))
        self.assertEquals(3, len(objects))
        
        objects = list(AwareModel.objects.from_schemata(a, b))
        self.assertEquals(6, len(objects))
    
    def test_ensure_multi_schema_fetched_objects_with_same_pk_differ(self):
        a = Schema.objects.create(name='a', schema='a')
        a.activate()
        AwareModel.objects.create(name='foo', pk=1)
        
        b = Schema.objects.create(name='b', schema='b')
        b.activate()
        AwareModel.objects.create(name='foo', pk=1)
        
        b.deactivate()
        
        objects = list(AwareModel.objects.from_schemata(a, b))
        self.assertEquals(2, len(objects))
        self.assertEquals(objects[0], objects[0])
        self.assertNotEquals(objects[0], objects[1], 'MultiSchemaManager should tag _schema attribute on models.')