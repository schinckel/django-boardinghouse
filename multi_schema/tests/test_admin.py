from django.test import TestCase
from django.contrib import admin

from ..schema import get_schema
from ..models import Schema, User
from .models import AwareModel

class TestAdminAdditions(TestCase):
    def test_ensure_schema_schema_is_not_editable(self):
        Schema.objects.mass_create('a','b','c')
        
        user = User.objects.create_superuser(
            username="su",
            password="su",
            email="su@example.com"
        )
        
        self.client.login(username='su', password='su')
        response = self.client.get('/admin/multi_schema/schema/a/')
        form = response.context['adminform'].form
        self.assertTrue('name' in form.fields)
        self.assertTrue('schema' not in form.fields, 'Schema.schema should be read-only on edit.')
        
        response = self.client.get('/admin/multi_schema/schema/add/')
        form = response.context['adminform'].form
        self.assertTrue('name' in form.fields)
        self.assertTrue('schema' in form.fields, 'Schema.schema should be editable on create.')
        