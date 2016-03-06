from django.test import TestCase
from django.contrib.auth.models import User, Permission

from boardinghouse.contrib.template.models import SchemaTemplate
from boardinghouse.schema import (
    activate_schema,
    _schema_exists,
    get_active_schema_name,
)

CREDENTIALS = {
    'username': 'username',
    'password': 'password'
}


class TestContribTemplate(TestCase):
    def test_templates_can_be_created(self):
        template = SchemaTemplate.objects.create(name='Foo')
        self.assertTrue(_schema_exists(template.schema))
        activate_schema(template.schema)
        self.assertEqual(get_active_schema_name(), template.schema)

    def test_templates_cannot_be_activated_normally(self):
        template = SchemaTemplate.objects.create(name='Foo')
        User.objects.create_user(**CREDENTIALS)
        self.client.login(**CREDENTIALS)
        response = self.client.get('/__change_schema__/{}/'.format(template.schema))
        self.assertEquals(403, response.status_code)

    def test_templates_can_be_activated_with_permission(self):
        template = SchemaTemplate.objects.create(name='Foo')
        user = User.objects.create_user(**CREDENTIALS)
        user.user_permissions.add(Permission.objects.get(codename='activate_schematemplate'))
        self.client.login(**CREDENTIALS)
        response = self.client.get('/__change_schema__/{}/'.format(template.schema))
        self.assertEquals(200, response.status_code)

    def test_cloning_templates_clones_data(self):
        pass

    def test_editing_template_does_not_change_template_data(self):
        pass
