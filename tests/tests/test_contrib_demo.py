from django.test import TestCase

from django.contrib.auth.models import User

from boardinghouse.contrib.demo.models import DemoSchema

CREDENTIALS = {
    'username': 'username',
    'password': 'password'
}


class TestContribDemo(TestCase):
    def test_demo_can_be_created_and_activated(self):
        user = User.objects.create_user(**CREDENTIALS)
        schema = DemoSchema.objects.create(user=user)
        schema.activate()
        schema.deactivate()

    def test_demo_can_only_be_activated_by_user(self):
        pass