from __future__ import unicode_literals

from django.test import TestCase
from django.utils import six
from django.core.urlresolvers import reverse
from django.contrib.auth.models import Permission

from boardinghouse.schema import get_schema_model

from ..models import AwareModel, NaiveModel, User

Schema = get_schema_model()


class TestAdminAdditions(TestCase):
    def test_ensure_schema_schema_is_not_editable(self):
        Schema.objects.mass_create('a', 'b', 'c')

        User.objects.create_superuser(
            username="su",
            password="su",
            email="su@example.com"
        )

        self.client.login(username='su', password='su')
        response = self.client.get(reverse('admin:boardinghouse_schema_change', args='a'))
        form = response.context['adminform'].form
        self.assertTrue('name' in form.fields)
        self.assertTrue('schema' not in form.fields, 'Schema.schema should be read-only on edit.')

        response = self.client.get(reverse('admin:boardinghouse_schema_add'))
        form = response.context['adminform'].form
        self.assertTrue('name' in form.fields)
        self.assertTrue('schema' in form.fields, 'Schema.schema should be editable on create.')

    def test_schema_aware_models_when_no_schema_selected(self):
        Schema.objects.mass_create('a', 'b', 'c')

        User.objects.create_superuser(
            username="su",
            password="su",
            email="su@example.com"
        )

        self.client.login(username='su', password='su')

        response = self.client.get(reverse('admin:tests_awaremodel_changelist'))
        # Should we handle this, and provide feedback?
        self.assertEqual(302, response.status_code)

    def test_schemata_list(self):
        from boardinghouse.admin import schemata

        user = User.objects.create_user(
            username='user', password='password', email='user@example.com'
        )
        Schema.objects.mass_create('a', 'b', 'c')
        self.assertEqual('', schemata(user))

        user.schemata.add(*Schema.objects.all())
        self.assertEqual(set(['a', 'b', 'c']), set(schemata(user).split('<br>')))

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
            object_repr=six.text_type(aware),
            change_message='test',
            action_flag=ADDITION,
        )

        entry = LogEntry.objects.get()

        self.assertEqual('a', entry.object_schema.pk)
        self.assertEqual(2, len(entry.get_admin_url().split('?')))
        self.assertEqual('__schema=a', entry.get_admin_url().split('?')[1])

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
            object_repr=six.text_type(naive),
            change_message='test',
            action_flag=ADDITION,
        )

        entry = LogEntry.objects.get()

        self.assertEqual(None, entry.object_schema_id)
        self.assertEqual(1, len(entry.get_admin_url().split('?')))

    def test_create_schema_with_contrib_template(self):
        pass

    def test_create_schema_without_contrib_template(self):
        pass


class TestAdminTemplate(TestCase):
    def test_admin_template_renders_switcher(self):
        user = User.objects.create_user(
            username='admin',
            password='password'
        )
        user.is_staff = True
        user.save()

        self.client.login(username='admin', password='password')

        Schema.objects.mass_create('a', 'b')
        user.schemata.add(Schema.objects.get(pk='a'))
        user.user_permissions.add(Permission.objects.get(codename='change_awaremodel'))

        self.client.get('/?__schema=a')
        response = self.client.get(reverse('admin:tests_awaremodel_changelist'))
        self.assertTemplateUsed(response, 'boardinghouse/change_schema.html')
