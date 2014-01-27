from django.test import TestCase

from ..schema import get_schema_model
from .models import AwareModel, NaiveModel

Schema = get_schema_model()

class TestPartitioning(TestCase):
    def test_aware_objects_are_created_in_active_schema(self):
        first = Schema.objects.create(name='first', schema='first')
        second = Schema.objects.create(name='second', schema='second')
        
        first.activate()
        foo = AwareModel.objects.create(name="Foo object")
        AwareModel.objects.create(name="Bar object")
        self.assertEquals(2, AwareModel.objects.count())
        
        second.activate()
        self.assertEquals(0, AwareModel.objects.count())
        AwareModel.objects.create(name="Baz object")
        self.assertRaises(AwareModel.DoesNotExist, AwareModel.objects.get, name='Foo object')
        
        # TODO: Make this work?
        # second.deactivate()
        # self.assertEquals(0, AwareModel.objects.count())
        
        first.activate()
        self.assertRaises(AwareModel.DoesNotExist, AwareModel.objects.get, name='Baz object')
        
    def test_boardinghouse_manager(self):
        first = Schema.objects.create(name='first', schema='first')
        second = Schema.objects.create(name='second', schema='second')
        
        first.activate()
        foo = AwareModel.objects.create(name="Foo object").name
        bar = AwareModel.objects.create(name="Bar object").name
        
        second.activate()
        baz = AwareModel.objects.create(name="Baz object").name
        
        second.deactivate()
        
        self.assertEquals(3, len(list(AwareModel.objects.from_schemata(Schema.objects.all()))))
        
        self.assertEquals([baz], [x.name for x in AwareModel.objects.from_schemata(second)])
        self.assertNotIn(baz, [x.name for x in AwareModel.objects.from_schemata(first)])
    
    def test_naive_objects_are_created_in_public_schema(self):
        first = Schema.objects.create(name='first', schema='first')
        second = Schema.objects.create(name='second', schema='second')
        
        NaiveModel.objects.create(name="Public")
        
        first.activate()
        self.assertEquals(1, NaiveModel.objects.count())
        NaiveModel.objects.create(name="First")
        
        second.activate()
        self.assertEquals(2, NaiveModel.objects.count())
        NaiveModel.objects.create(name="Second")
        
        second.deactivate()
        self.assertEquals(3, NaiveModel.objects.count())
