from django.test import TestCase
from django.db.migrations.state import ProjectState
from django.db import connection, migrations, transaction

from boardinghouse.models import Schema

from ..models import AwareModel, ViewBackedModel


class TestCloneSchemaDBFunction(TestCase):
    def test_clone_schema_with_trigger(self):
        TRIGGER_FUNCTION = '''CREATE FUNCTION trigger_this()
                              RETURNS TRIGGER AS $$
                                BEGIN
                                  RAISE EXCEPTION 'Trigger fired correctly';
                                END;
                              $$
                              LANGUAGE PLPGSQL'''
        TRIGGER_TRIGGER = '''CREATE TRIGGER "test_trigger_this"
                             BEFORE INSERT ON tests_awaremodel
                             FOR EACH STATEMENT
                             EXECUTE PROCEDURE trigger_this()'''
        project_state = ProjectState()
        new_state = project_state.clone()

        trigger_function_op = migrations.RunSQL(
            sql=TRIGGER_FUNCTION,
            reverse_sql='DROP FUNCTION trigger_this()'
        )
        trigger_op = migrations.RunSQL(
            sql=TRIGGER_TRIGGER,
            reverse_sql='DROP TRIGGER "test_trigger_this" BEFORE EACH UPDATE ON tests_awaremodel'
        )

        trigger_function_op.state_forwards('tests', new_state)
        trigger_op.state_forwards('tests', new_state)

        with connection.schema_editor() as editor:
            trigger_function_op.database_forwards('tests', editor, project_state, new_state)
            trigger_op.database_forwards('tests', editor, project_state, new_state)

        Schema.objects.mass_create('a', 'b', 'c')

        for schema in Schema.objects.all():
            schema.activate()
            with transaction.atomic():
                with self.assertRaises(Exception) as exc:
                    self.assertTrue('Trigger fired correctly' == exc.args[0])
                    AwareModel.objects.create(name='FAILCREATE')

    def test_cloning_template_with_view(self):
        schema = Schema.objects.create(name='a', schema='a')
        schema.activate()

        self.assertEqual(1000, ViewBackedModel.objects.count())

    def test_cloning_template_with_function(self):
        pass
