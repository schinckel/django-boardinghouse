from django.test import TestCase

from ..schema import get_schema
from ..models import Schema, User
from .models import AwareModel

class TestMiddlewareInstalled(TestCase):
    def test_view_without_schema_aware_models_works_without_activation(self):
        resp = self.client.get('/')
        self.assertEquals(200, resp.status_code)
        self.assertEquals('None', resp.content)
    
    
    def test_unauth_cannot_change_schema(self):
        first = Schema.objects.create(name='first', schema='first')
        second = Schema.objects.create(name='second', schema='second')
        
        resp = self.client.get('/', HTTP_X_CHANGE_SCHEMA='first')
        self.assertEquals('None', resp.content)
        
    
    def test_invalid_schema(self):
        first = Schema.objects.create(name='first', schema='first')
        second = Schema.objects.create(name='second', schema='second')
        
        user = User.objects.create_superuser(
            username="su",
            password="su",
            email="su@example.com"
        )
        self.client.login(username='su', password='su')
        
        resp = self.client.get('/', HTTP_X_CHANGE_SCHEMA='third')
        self.assertEquals('None', resp.content)
        
        resp = self.client.get('/', HTTP_X_CHANGE_SCHEMA='second')
        self.assertEquals('second', resp.content)
        
        self.client.get('/__change_schema__/third/')
        resp = self.client.get('/')
        self.assertEquals('None', resp.content)
    
    
    def test_only_one_available_schema(self):
        first = Schema.objects.create(name='first', schema='first')
        self.assertEquals(1, Schema.objects.count())
        
        user = User.objects.create_superuser(
            username="su",
            password="su",
            email="su@example.com"
        )
        self.client.login(username='su', password='su')
        resp = self.client.get('/')
        self.assertEquals('first', resp.content)

        
    def test_middleware_activation(self):
        first = Schema.objects.create(name='first', schema='first')
        second = Schema.objects.create(name='second', schema='second')
        
        user = User.objects.create_superuser(
            username="su",
            password="su",
            email="su@example.com"
        )
        
        self.client.login(username='su', password='su')
                
        self.client.get('/__change_schema__/second/')
        resp = self.client.get('/')
        self.assertEquals('second', resp.content)
        
        resp = self.client.get('/', {'__schema':'first'}, follow=True)
        self.assertEquals('first', resp.content)
        
        resp = self.client.get('/', {'__schema':'second', 'foo': 'bar'}, follow=True)
        self.assertEquals('second\nfoo=bar', resp.content)
        
        resp = self.client.get('/', HTTP_X_CHANGE_SCHEMA='first')
        self.assertEquals('first', resp.content)
        