import unittest

from django.db import connection, models, migrations
from django.db.migrations.migration import Migration
from django.db.migrations.state import ProjectState
from django.db.transaction import atomic
from django.db.utils import IntegrityError
from django.test import TransactionTestCase
from django.utils import six

from boardinghouse.schema import get_schema_model, get_template_schema

Schema = get_schema_model()
template_schema = get_template_schema()

COLUMN_SQL = """
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = '%(table_name)s'
AND table_schema = '%(table_schema)s'
AND column_name = '%(column_name)s';
"""


def all_schemata(test):
    def inner(self, *args, **kwargs):
        with connection.cursor() as cursor:
            cursor.execute('SET search_path TO __template__,public')
        test(self, *args, **kwargs)
        for schema in Schema.objects.all():
            schema.activate()
            test(self, *args, **kwargs)
            schema.deactivate()
    return inner


class MigrationTestBase(TransactionTestCase):
    """
    Contains an extended set of asserts for testing migrations and schema operations.
    """

    available_apps = [
        "boardinghouse",
        "tests",
        "django.contrib.auth",
        "django.contrib.admin",
        "django.contrib.contenttypes",
    ]

    def get_table_description(self, table):
        with connection.cursor() as cursor:
            return connection.introspection.get_table_description(cursor, table)

    def get_table_list(self):
        with connection.cursor() as cursor:
            table_list = connection.introspection.get_table_list(cursor)
        if table_list and not isinstance(table_list[0], six.string_types):
            table_list = [table.name for table in table_list]
        return table_list

    @all_schemata
    def assertTableExists(self, table):
        self.assertIn(table, self.get_table_list())

    @all_schemata
    def assertTableNotExists(self, table):
        self.assertNotIn(table, self.get_table_list())

    @all_schemata
    def assertColumnExists(self, table, column):
        self.assertIn(column, [c.name for c in self.get_table_description(table)])

    @all_schemata
    def assertColumnNotExists(self, table, column):
        self.assertNotIn(column, [c.name for c in self.get_table_description(table)])

    @all_schemata
    def assertColumnNull(self, table, column):
        self.assertEqual([c.null_ok for c in self.get_table_description(table) if c.name == column][0], True)

    @all_schemata
    def assertColumnNotNull(self, table, column):
        self.assertEqual([c.null_ok for c in self.get_table_description(table) if c.name == column][0], False)

    @all_schemata
    def assertIndexExists(self, table, columns, value=True):
        with connection.cursor() as cursor:
            self.assertEqual(
                value,
                any(
                    c["index"]
                    for c in connection.introspection.get_constraints(cursor, table).values()
                    if c['columns'] == list(columns)
                ),
            )

    @all_schemata
    def assertIndexNotExists(self, table, columns):
        return self.assertIndexExists(table, columns, False)

    @all_schemata
    def assertFKExists(self, table, columns, to, value=True):
        with connection.cursor() as cursor:
            self.assertEqual(
                value,
                any(
                    c["foreign_key"] == to
                    for c in connection.introspection.get_constraints(cursor, table).values()
                    if c['columns'] == list(columns)
                ),
            )

    @all_schemata
    def assertFKNotExists(self, table, columns, to, value=True):
        return self.assertFKExists(table, columns, to, False)

    def apply_operations(self, app_label, project_state, operations):
        migration = Migration('name', app_label)
        migration.operations = operations
        with connection.schema_editor() as editor:
            return migration.apply(project_state, editor)

    def unapply_operations(self, app_label, project_state, operations):
        migration = Migration('name', app_label)
        migration.operations = operations
        with connection.schema_editor() as editor:
            return migration.unapply(project_state, editor)

    def set_up_test_model(self):
        operations = [
            migrations.CreateModel(
                "Pony",
                [
                    ('pony_id', models.AutoField(primary_key=True)),
                    ('pink', models.IntegerField(default=3)),
                    ('weight', models.FloatField())
                ],
            ),
            migrations.CreateModel(
                'Rider',
                [
                    ('rider_id', models.AutoField(primary_key=True)),
                    ('pony', models.ForeignKey('Pony'))
                ],
            ),
        ]
        return self.apply_operations('tests', ProjectState(), operations)


class TestMigrations(MigrationTestBase):
    """
    This is all about testing that operations have been performed on all
    available schemata. To that end, we create three schemata in the setUp,
    and drop them in the tearDown. We also use the class above that has wrapped
    the various new tests in code that performs the test on each schema.
    """

    def setUp(self):
        Schema.objects.mass_create('a', 'b', 'c')

    def tearDown(self):
        with connection.cursor() as cursor:
            for schema in Schema.objects.all():
                cursor.execute('DROP SCHEMA IF EXISTS {} CASCADE'.format(schema.schema))

            cursor.execute('SET search_path TO __template__,public')
            cursor.execute('DROP TABLE IF EXISTS tests_rider')
            cursor.execute("DROP TABLE IF EXISTS tests_pony")

    def test_create_model(self):
        operation = migrations.CreateModel("Pony", [
            ('pony_id', models.AutoField(primary_key=True)),
            ('pink', models.IntegerField(default=1)),
        ])
        project_state = ProjectState()
        new_state = project_state.clone()
        operation.state_forwards('tests', new_state)
        self.assertTableNotExists('tests_pony')
        with connection.schema_editor() as editor:
            operation.database_forwards('tests', editor, project_state, new_state)
        self.assertTableExists('tests_pony')
        with connection.schema_editor() as editor:
            operation.database_backwards('tests', editor, new_state, project_state)
        self.assertTableNotExists('tests_pony')

    def test_delete_model(self):
        project_state = self.set_up_test_model()
        operation = migrations.DeleteModel("Pony")
        new_state = project_state.clone()
        operation.state_forwards('tests', new_state)
        self.assertTableExists('tests_pony')
        with connection.schema_editor() as editor:
            operation.database_forwards('tests', editor, project_state, new_state)
        self.assertTableNotExists('tests_pony')
        with connection.schema_editor() as editor:
            operation.database_backwards('tests', editor, new_state, project_state)
        self.assertTableExists('tests_pony')

    def test_rename_model(self):
        project_state = self.set_up_test_model()
        operation = migrations.RenameModel("Pony", "Horse")
        new_state = project_state.clone()
        operation.state_forwards('tests', new_state)
        self.assertTableExists('tests_pony')
        self.assertTableNotExists('tests_horse')
        with connection.schema_editor() as editor:
            operation.database_forwards('tests', editor, project_state, new_state)
        self.assertTableExists('tests_horse')
        self.assertTableNotExists('tests_pony')
        with connection.schema_editor() as editor:
            operation.database_backwards('tests', editor, new_state, project_state)
        self.assertTableExists('tests_pony')
        self.assertTableNotExists('tests_horse')

    def test_add_field(self):
        project_state = self.set_up_test_model()
        operation = migrations.AddField(
            'Pony',
            'height',
            models.FloatField(null=True, default=5)
        )
        new_state = project_state.clone()
        operation.state_forwards('tests', new_state)
        self.assertColumnNotExists('tests_pony', 'height')
        with connection.schema_editor() as editor:
            operation.database_forwards('tests', editor, project_state, new_state)
        self.assertColumnExists('tests_pony', 'height')
        with connection.schema_editor() as editor:
            operation.database_backwards('tests', editor, new_state, project_state)
        self.assertColumnNotExists('tests_pony', 'height')

    def test_remove_field(self):
        project_state = self.set_up_test_model()
        operation = migrations.RemoveField('Pony', 'pink')
        new_state = project_state.clone()
        operation.state_forwards('tests', new_state)
        self.assertColumnExists('tests_pony', 'pink')
        with connection.schema_editor() as editor:
            operation.database_forwards('tests', editor, project_state, new_state)
        self.assertColumnNotExists('tests_pony', 'pink')
        with connection.schema_editor() as editor:
            operation.database_backwards('tests', editor, new_state, project_state)
        self.assertColumnExists('tests_pony', 'pink')

    def test_alter_model_table(self):
        project_state = self.set_up_test_model()
        operation = migrations.AlterModelTable('Pony', 'tests_pony_2')
        new_state = project_state.clone()
        operation.state_forwards('tests', new_state)
        self.assertTableExists('tests_pony')
        self.assertTableNotExists('tests_pony_2')
        with connection.schema_editor() as editor:
            operation.database_forwards('tests', editor, project_state, new_state)
        self.assertTableExists('tests_pony_2')
        self.assertTableNotExists('tests_pony')
        with connection.schema_editor() as editor:
            operation.database_backwards('tests', editor, new_state, project_state)
        self.assertTableExists('tests_pony')
        self.assertTableNotExists('tests_pony_2')

    def test_alter_field(self):
        project_state = self.set_up_test_model()
        operation = migrations.AlterField('Pony', 'pink', models.IntegerField(null=True))
        new_state = project_state.clone()
        operation.state_forwards('tests', new_state)
        self.assertColumnNotNull('tests_pony', 'pink')
        with connection.schema_editor() as editor:
            operation.database_forwards('tests', editor, project_state, new_state)
        self.assertColumnNull('tests_pony', 'pink')
        with connection.schema_editor() as editor:
            operation.database_backwards('tests', editor, new_state, project_state)
        self.assertColumnNotNull('tests_pony', 'pink')

    def test_rename_field(self):
        project_state = self.set_up_test_model()
        operation = migrations.RenameField('Pony', 'pink', 'rosa')
        new_state = project_state.clone()
        operation.state_forwards('tests', new_state)
        self.assertColumnExists('tests_pony', 'pink')
        self.assertColumnNotExists('tests_pony', 'rosa')
        with connection.schema_editor() as editor:
            operation.database_forwards('tests', editor, project_state, new_state)
        self.assertColumnNotExists('tests_pony', 'pink')
        self.assertColumnExists('tests_pony', 'rosa')
        with connection.schema_editor() as editor:
            operation.database_backwards('tests', editor, new_state, project_state)
        self.assertColumnExists('tests_pony', 'pink')
        self.assertColumnNotExists('tests_pony', 'rosa')

    def test_alter_unique_together(self):
        project_state = self.set_up_test_model()
        operation = migrations.AlterUniqueTogether('Pony', [('pink', 'weight')])
        new_state = project_state.clone()
        operation.state_forwards('tests', new_state)

        @all_schemata
        def insert(cursor):
            cursor.execute('INSERT INTO tests_pony (pink, weight) VALUES (1, 1)')
            cursor.execute('INSERT INTO tests_pony (pink, weight) VALUES (1, 1)')
            cursor.execute('DELETE FROM tests_pony')

        @all_schemata
        def insert_fail(cursor):
            cursor.execute('INSERT INTO tests_pony (pink, weight) VALUES (1, 1)')
            with self.assertRaises(IntegrityError):
                with atomic():
                    cursor.execute('INSERT INTO tests_pony (pink, weight) VALUES (1, 1)')
            cursor.execute('DELETE FROM tests_pony')

        with connection.cursor() as cursor:
            insert(cursor)
            with connection.schema_editor() as editor:
                operation.database_forwards('tests', editor, project_state, new_state)
            insert_fail(cursor)
            with connection.schema_editor() as editor:
                operation.database_backwards('tests', editor, new_state, project_state)
            insert(cursor)

    def test_alter_index_together(self):
        project_state = self.set_up_test_model()
        operation = migrations.AlterIndexTogether('Pony', [('pink', 'weight')])
        new_state = project_state.clone()
        operation.state_forwards('tests', new_state)
        self.assertIndexNotExists('tests_pony', ['pink', 'weight'])
        with connection.schema_editor() as editor:
            operation.database_forwards('tests', editor, project_state, new_state)
        self.assertIndexExists('tests_pony', ['pink', 'weight'])
        with connection.schema_editor() as editor:
            operation.database_backwards('tests', editor, new_state, project_state)
        self.assertIndexNotExists('tests_pony', ['pink', 'weight'])

    def test_alter_order_with_respect_to(self):
        project_state = self.set_up_test_model()
        operation = migrations.AlterOrderWithRespectTo('Rider', 'pony')
        new_state = project_state.clone()
        operation.state_forwards('tests', new_state)
        self.assertColumnNotExists('tests_rider', '_order')
        with connection.schema_editor() as editor:
            operation.database_forwards('tests', editor, project_state, new_state)
        self.assertColumnExists('tests_rider', '_order')
        with connection.schema_editor() as editor:
            operation.database_backwards('tests', editor, new_state, project_state)
        self.assertColumnNotExists('tests_rider', '_order')

    def test_run_sql(self):
        project_state = self.set_up_test_model()
        operation = migrations.RunSQL("""
CREATE TABLE i_love_ponies (id int, special_thing int);
CREATE INDEX i_love_ponies_special_idx ON i_love_ponies (special_thing);
INSERT INTO i_love_ponies (id, special_thing) VALUES (1, 42);
INSERT INTO i_love_ponies (id, special_thing) VALUES (2, 51), (3, 60);
""",
" DROP TABLE i_love_ponies")
        new_state = project_state.clone()
        operation.state_forwards('tests', new_state)
        self.assertTableNotExists('i_love_ponies')
        with connection.schema_editor() as editor:
            operation.database_forwards('tests', editor, project_state, new_state)
        self.assertTableExists('i_love_ponies')
        self.assertIndexExists('i_love_ponies', ['special_thing'])
        with connection.schema_editor() as editor:
            operation.database_backwards('tests', editor, new_state, project_state)
        self.assertTableNotExists('i_love_ponies')

    @unittest.expectedFailure
    def test_run_python(self):
        """
        Because this can run arbitrary python code, we can't know
        which parts of it need to run against each schema, and which
        parts run against the public schema.

        We could hack into any generated SQL, and inspect it, looking
        for table names, attempting to push data to the correct
        schemata (including executing the SQL multiple times if
        necessary).

        Maybe we could fuck with the models generated by project_state.render(),
        and make their generated SQL do what we need it to do. Although, it looks
        like Pony.objects is a normal models.Manager class.
        """

        project_state = self.set_up_test_model()

        def forwards(models, schema_editor):
            Pony = models.get_model('tests', 'Pony')
            Pony.objects.create(pink=1, weight=3.55)
            Pony.objects.create(weight=5)

        def backwards(models, schema_editor):
            Pony = models.get_model('tests', 'Pony')
            Pony.objects.filter(pink=1, weight=3.55).delete()
            Pony.objects.filter(weight=5).delete()

        operation = migrations.RunPython(forwards, reverse_code=backwards)
        new_state = project_state.clone()
        operation.state_forwards('tests', new_state)

        Pony = project_state.render().get_model('tests', 'Pony')
        all_schemata(lambda x: self.assertFalse(Pony.objects.exists()))
        with connection.schema_editor() as editor:
            operation.database_forwards('tests', editor, project_state, new_state)
        all_schemata(lambda x: self.assertEqual(2, Pony.objects.count(), 'Incorrect number of Ponies found in schema {}'.format(schema.schema)))
        with connection.schema_editor() as editor:
            operation.database_backwards('tests', editor, new_state, project_state)
        all_schemata(lambda x: self.assertFalse(Pony.objects.exists()))
