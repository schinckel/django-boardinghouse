from django.test import TestCase

from django.contrib.auth.models import User
from django.db import migrations, models, connection
from django.db.migrations.state import ProjectState
from django.utils import timezone

from .utils import get_table_list

from boardinghouse.contrib.demo.models import DemoSchema, DemoSchemaExpired

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

    def test_activation_of_expired_demo_raises(self):
        user = User.objects.create_user(**CREDENTIALS)
        schema = DemoSchema.objects.create(user=user, expiry_date=timezone.now())
        with self.assertRaises(DemoSchemaExpired):
            schema.activate()

    def test_cleanup_expired_removes_expired(self):
        pass

    def test_demo_schemata_get_migrated(self):
        user = User.objects.create_user(**CREDENTIALS)
        schema = DemoSchema.objects.create(user=user)

        operation = migrations.CreateModel("Pony", [
            ('pony_id', models.AutoField(primary_key=True)),
            ('pink', models.IntegerField(default=1)),
        ])
        project_state = ProjectState()
        new_state = project_state.clone()
        operation.state_forwards('tests', new_state)

        schema.activate()
        self.assertFalse('tests_pony' in get_table_list())

        with connection.schema_editor() as editor:
            operation.database_forwards('tests', editor, project_state, new_state)
        schema.activate()
        self.assertTrue('tests_pony' in get_table_list())

        with connection.schema_editor() as editor:
            operation.database_backwards('tests', editor, new_state, project_state)
        schema.activate()
        self.assertFalse('tests_pony' in get_table_list())

    def test_default_expiry_period_from_settings(self):
        pass

    def test_custom_expiry_period(self):
        pass
