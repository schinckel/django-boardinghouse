from django.test import TestCase

from .models import AwareModel, NaiveModel
from ..templatetags.boardinghouse import *

class TestTemplateTags(TestCase):
    def test_is_schema_aware_filter(self):
        self.assertTrue(is_schema_aware(AwareModel()))
        self.assertFalse(is_schema_aware(NaiveModel()))
    
    def test_is_shared_model_filter(self):
        self.assertFalse(is_shared_model(AwareModel()))
        self.assertTrue(is_shared_model(NaiveModel()))
        
    def test_schema_name_filter(self):
        Schema.objects.create(name='Schema Name', schema='foo')
        self.assertEquals('Schema Name', schema_name('foo'))
        self.assertEquals('no schema', schema_name(None))
        self.assertEquals('no schema', schema_name(''))
        self.assertEquals('no schema', schema_name(False))
        self.assertEquals('no schema', schema_name('foobar'))
        self.assertEquals('no schema', schema_name('foo_'))
        self.assertEquals('no schema', schema_name('foofoo'))