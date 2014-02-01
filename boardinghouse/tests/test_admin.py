import unittest

from django.test import TestCase
from django.contrib import admin, auth
from django.core.urlresolvers import reverse

from ..schema import get_schema_model
from .models import AwareModel, NaiveModel, User

Schema = get_schema_model()

class TestAdminAdditions(TestCase):
    def test_ensure_schema_schema_is_not_editable(self):
        Schema.objects.mass_create('a','b','c')
        
        user = User.objects.create_superuser(
            username="su",
            password="su",
            email="su@example.com"
        )
        
        self.client.login(username='su', password='su')
        response = self.client.get('/admin/boardinghouse/schema/a/')
        form = response.context['adminform'].form
        self.assertTrue('name' in form.fields)
        self.assertTrue('schema' not in form.fields, 'Schema.schema should be read-only on edit.')
        
        response = self.client.get('/admin/boardinghouse/schema/add/')
        form = response.context['adminform'].form
        self.assertTrue('name' in form.fields)
        self.assertTrue('schema' in form.fields, 'Schema.schema should be editable on create.')
    
    def test_schema_aware_models_when_no_schema_selected(self):
        Schema.objects.mass_create('a','b','c')
        
        user = User.objects.create_superuser(
            username="su",
            password="su",
            email="su@example.com"
        )
        
        self.client.login(username='su', password='su')
        
        response = self.client.get('/admin/boardinghouse/awaremodel/')
        # Should we handle this, and provide feedback?
        self.assertEquals(449, response.status_code)
    
    def test_schemata_list(self):
        from boardinghouse.admin import schemata
        
        user = User.objects.create_user(
            username='user', password='password', email='user@example.com'
        )
        Schema.objects.mass_create('a','b','c')
        self.assertEquals('', schemata(user))
        
        user.schemata.add(*Schema.objects.all())
        self.assertEquals('a<br>b<br>c', schemata(user))
    
    def test_admin_log_includes_schema(self):
        from django.contrib.admin.models import LogEntry, ADDITION
        from django.contrib.contenttypes.models import ContentType
        
        Schema.objects.mass_create('a')
        schema = Schema.objects.get(name='a')
        schema.activate()
        
        aware = AwareModel.objects.create(name='foo')
        user = User.objects.create_user(username='test', password='test')
        
        LogEntry.objects.log_action(
            user_id=user.pk,
            content_type_id=ContentType.objects.get_for_model(aware).pk,
            object_id=aware.pk,
            object_repr=unicode(aware),
            change_message='test',
            action_flag=ADDITION,
        )
        
        entry = LogEntry.objects.get()
        
        self.assertEquals('a', entry.object_schema.pk)
        
        self.assertEquals('?__schema=a', entry.get_admin_url()[-11:])
    
    def test_admin_log_naive_object_no_schema(self):
        from django.contrib.admin.models import LogEntry, ADDITION
        from django.contrib.contenttypes.models import ContentType
        
        Schema.objects.mass_create('a')
        schema = Schema.objects.get(name='a')
        schema.activate()
        
        naive = NaiveModel.objects.create(name='foo')
        user = User.objects.create_user(username='test', password='test')
        
        LogEntry.objects.log_action(
            user_id=user.pk,
            content_type_id=ContentType.objects.get_for_model(naive).pk,
            object_id=naive.pk,
            object_repr=unicode(naive),
            change_message='test',
            action_flag=ADDITION,
        )
        
        entry = LogEntry.objects.get()
        
        self.assertEquals(None, entry.object_schema_id)