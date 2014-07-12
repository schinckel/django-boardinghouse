from __future__ import unicode_literals

from unittest import TestCase

from django.test import Client

from boardinghouse.schema import get_schema_model
from ..models import AwareModel, User

Schema = get_schema_model()


class TestMultipleClients(TestCase):
    def test_simultaneous_access(self):
        schema_a = Schema.objects.create(name='a', schema='a')
        schema_b = Schema.objects.create(name='b', schema='b')

        user_a = User.objects.create_user(
            username='a', email='a@example.com', password='a'
        )
        user_b = User.objects.create_user(
            username='b', email='b@example.com', password='b'
        )

        schema_a.activate()
        AwareModel.objects.create(name='foo')
        schema_b.activate()
        AwareModel.objects.create(name='bar')

        schema_a.users.add(user_a)
        schema_b.users.add(user_b)

        client_a = Client()
        client_a.login(username='a', password='a')

        client_b = Client()
        client_b.login(username='b', password='b')

        resp = client_a.get('/aware/')
        self.assertEquals(b'foo', resp.content)

        resp = client_b.get('/aware/')
        self.assertEquals(b'bar', resp.content)

        resp = client_a.get('/aware/')
        self.assertEquals(b'foo', resp.content)
