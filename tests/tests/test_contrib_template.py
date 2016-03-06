from django.test import TestCase

from boardinghouse.contrib.template.models import SchemaTemplate
from boardinghouse.schema import (
    activate_schema,
    _schema_exists,
    get_active_schema_name,
)


class TestContribTemplate(TestCase):
    def test_templates_can_be_created(self):
        template = SchemaTemplate.objects.create(name='Foo')
        self.assertTrue(_schema_exists(template.schema))
        activate_schema(template.schema)
        self.assertEqual(get_active_schema_name(), template.schema)

    def test_templates_cannot_be_activated_normally(self):
        pass

    def test_cloning_templates_clones_data(self):
        pass

    def test_editing_template_does_not_change_template_data(self):
        pass
