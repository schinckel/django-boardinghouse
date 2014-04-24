from django.test import TestCase
from django.contrib.auth.models import User
from django.core.cache import cache

from ..models import Schema
from ..schema import get_active_schemata, get_all_schemata

class TestUserSchemataCache(TestCase):
    def test_adding_schema_to_user_clears_cache(self):
        User.objects.create_user(username='a', email='a@example.com', password='a')
        Schema.objects.mass_create('a','b','c')
        
        user = User.objects.get(username='a')
        self.assertEquals(0, len(user.visible_schemata))
        
        self.assertEquals([], list(cache.get('visible-schemata-%s' % user.pk)))
        
        user.schemata.add(Schema.objects.get(schema='a'))
        self.assertEquals(None, cache.get('visible-schemata-%s' % user.pk))
    
    def test_removing_schema_from_user_clears_cache(self):
        User.objects.create_user(username='a', email='a@example.com', password='a')
        Schema.objects.mass_create('a','b','c')
        
        user = User.objects.get(username='a')
        user.schemata.add(*Schema.objects.all())
        
        self.assertEquals(3, len(user.visible_schemata))
        
        user.schemata.remove(Schema.objects.get(schema='a'))
        self.assertEquals(None, cache.get('visible-schemata-%s' % user.pk))
    
    def test_adding_users_to_schema_clears_cache(self):
        User.objects.create_user(username='a', email='a@example.com', password='a')
        Schema.objects.mass_create('a','b','c')
        
        user = User.objects.get(username='a')
        
        self.assertEquals(0, len(user.visible_schemata))
        self.assertEquals([], list(cache.get('visible-schemata-%s' % user.pk)))
        
        schema = Schema.objects.get(schema='a')
        schema.users.add(user)
        
        self.assertEquals(None, cache.get('visible-schemata-%s' % user.pk))
    
    def test_removing_users_from_schema_clears_cache(self):
        User.objects.create_user(username='a', email='a@example.com', password='a')
        Schema.objects.mass_create('a','b','c')
        
        user = User.objects.get(username='a')
        user.schemata.add(*Schema.objects.all())
        self.assertEquals(3, len(user.visible_schemata))
        
        schema = Schema.objects.get(schema='a')
        schema.users.remove(user)
        
        self.assertEquals(None, cache.get('visible-schemata-%s' % user.pk))
    
    def test_saving_schema_clears_cache_for_related_users(self):
        User.objects.create_user(username='a', email='a@example.com', password='a')
        Schema.objects.mass_create('a','b','c')
        
        user = User.objects.get(username='a')
        user.schemata.add(*Schema.objects.all())
        
        self.assertEquals(3, len(user.visible_schemata))
        
        Schema.objects.get(schema='a').save()
        
        self.assertEquals(None, cache.get('visible-schemata-%s' % user.pk))
    
    def test_saving_schema_clears_global_active_schemata_cache(self):
        Schema.objects.mass_create('a','b','c')
        
        schema = Schema.objects.get(schema='a')
        
        self.assertEquals(3, len(get_all_schemata()))
        self.assertEquals(3, len(get_active_schemata()))
        
        schema.is_active = False
        schema.save()
        
        self.assertEquals(None, cache.get('active-schemata'))
        self.assertEquals(None, cache.get('all-schemata'))