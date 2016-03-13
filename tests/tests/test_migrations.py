import unittest

from django.apps import apps
from django.db import connection, models, migrations
from django.db.migrations.migration import Migration
from django.db.migrations.state import ProjectState
from django.db.transaction import atomic
from django.db.utils import IntegrityError
from django.test import TransactionTestCase
from django.utils import six

from boardinghouse.schema import get_schema_model, get_template_schema
from boardinghouse.schema import activate_template_schema, deactivate_schema
from boardinghouse.backends.postgres.schema import get_constraints
from boardinghouse.operations import AddField

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
        activate_template_schema()
        test(self, *args, schema='__template__', **kwargs)
        for schema in Schema.objects.all():
            schema.activate()
            test(self, *args, schema=schema.schema, **kwargs)
        deactivate_schema()
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
    def assertTableExists(self, table, **kwargs):
        self.assertIn(table, self.get_table_list())

    @all_schemata
    def assertTableNotExists(self, table, **kwargs):
        self.assertNotIn(table, self.get_table_list())

    @all_schemata
    def assertColumnExists(self, table, column, **kwargs):
        self.assertIn(column, [c.name for c in self.get_table_description(table)])

    @all_schemata
    def assertColumnNotExists(self, table, column, **kwargs):
        self.assertNotIn(column, [c.name for c in self.get_table_description(table)])

    @all_schemata
    def assertColumnNull(self, table, column, **kwargs):
        self.assertEqual([c.null_ok for c in self.get_table_description(table) if c.name == column][0], True)

    @all_schemata
    def assertColumnNotNull(self, table, column, **kwargs):
        self.assertEqual([c.null_ok for c in self.get_table_description(table) if c.name == column][0], False)

    @all_schemata
    def assertConstraint(self, table, columns, constraint_type, value=True, **kwargs):
        with connection.cursor() as cursor:
            constraints = get_constraints(cursor, table, kwargs['schema'])
            self.assertEqual(value,
                             any(c[constraint_type] for c in constraints.values()
                                 if set(c['columns']) == set(columns)))

    # These will get the all_schemata from the inner call
    def assertNoConstraint(self, table, columns, constraint_type, **kwargs):
        return self.assertConstraint(table, columns, constraint_type, value=False, **kwargs)

    def assertIndexExists(self, table, columns, value=True, **kwargs):
        return self.assertConstraint(table, columns, constraint_type='index', value=True, **kwargs)

    def assertIndexNotExists(self, table, columns, **kwargs):
        return self.assertConstraint(table, columns, constraint_type='index', value=False, **kwargs)

    def assertFKExists(self, table, columns, to, **kwargs):
        return self.assertConstraint(table, columns, constraint_type='foreign_key', value=to, **kwargs)

    def assertFKNotExists(self, table, columns, to, value=True, **kwargs):
        return self.assertConstraint(table, columns, constraint_type='foreign_key', value=False, **kwargs)

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

    def test_remove_foreign_key_field(self):
        project_state = self.set_up_test_model()
        operation = migrations.RemoveField('Rider', 'pony')
        new_state = project_state.clone()
        operation.state_forwards('tests', new_state)
        self.assertColumnExists('tests_rider', 'pony_id')
        with connection.schema_editor() as editor:
            operation.database_forwards('tests', editor, project_state, new_state)
        self.assertColumnNotExists('tests_rider', 'pony_id')
        with connection.schema_editor() as editor:
            operation.database_backwards('tests', editor, new_state, project_state)
        self.assertColumnExists('tests_rider', 'pony_id')

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
        def insert(cursor, **kwargs):
            cursor.execute('INSERT INTO tests_pony (pink, weight) VALUES (1, 1)')
            cursor.execute('INSERT INTO tests_pony (pink, weight) VALUES (1, 1)')
            cursor.execute('DELETE FROM tests_pony')

        @all_schemata
        def insert_fail(cursor, **kwargs):
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

    def test_add_check_constraint(self):
        project_state = self.set_up_test_model()
        operation = migrations.AlterField(
            model_name='pony',
            name='pink',
            field=models.PositiveIntegerField(default=3)
        )
        new_state = project_state.clone()
        operation.state_forwards('tests', new_state)

        self.assertNoConstraint('tests_pony', ['pink'], 'check')

        with connection.schema_editor() as editor:
            operation.database_forwards('tests', editor, project_state, new_state)

        self.assertConstraint('tests_pony', ['pink'], 'check')

        with connection.schema_editor() as editor:
            operation.database_backwards('tests', editor, new_state, project_state)

        self.assertNoConstraint('tests_pony', ['pink'], 'check')

    def test_add_unique_constraint(self):
        project_state = self.set_up_test_model()
        operation = migrations.AlterField(
            model_name='pony',
            name='pink',
            field=models.IntegerField(unique=True, default=3)
        )
        new_state = project_state.clone()
        operation.state_forwards('tests', new_state)

        self.assertNoConstraint('tests_pony', ['pink'], 'unique')

        with connection.schema_editor() as editor:
            operation.database_forwards('tests', editor, project_state, new_state)

        self.assertConstraint('tests_pony', ['pink'], 'unique')

        with connection.schema_editor() as editor:
            operation.database_backwards('tests', editor, new_state, project_state)

        self.assertNoConstraint('tests_pony', ['pink'], 'unique')

    def test_run_sql(self):
        project_state = self.set_up_test_model()
        operation = migrations.RunSQL("""
            CREATE TABLE i_love_ponies (id int, special_thing int);
            CREATE INDEX i_love_ponies_special_idx ON i_love_ponies (special_thing);
            INSERT INTO i_love_ponies (id, special_thing) VALUES (1, 42);
            INSERT INTO i_love_ponies (id, special_thing) VALUES (2, 51), (3, 60);
            DELETE FROM i_love_ponies WHERE special_thing = 42;
            UPDATE i_love_ponies SET special_thing = 42 WHERE id = 2;
            """,
            " DROP TABLE i_love_ponies")
        new_state = project_state.clone()
        operation.state_forwards('tests', new_state)
        self.assertTableNotExists('i_love_ponies')
        with connection.schema_editor() as editor:
            operation.database_forwards('tests', editor, project_state, new_state)
        self.assertTableExists('i_love_ponies')
        self.assertIndexExists('i_love_ponies', ['special_thing'])

        @all_schemata
        def objects_exist(cursor, **kwargs):
            cursor = connection.cursor()
            cursor.execute('SELECT * FROM i_love_ponies ORDER BY id')
            result = cursor.fetchmany(4)
            self.assertTrue(result, 'No objects found in {schema}'.format(**kwargs))
            expected = [(2, 42), (3, 60)]
            self.assertEqual(
                sorted(expected),
                sorted(result),
                'Mismatch objects found in schema {schema}: expected {0}, saw {1}'
                .format(expected, result, **kwargs)
            )

        with connection.cursor() as cursor:
            objects_exist(cursor)

        with connection.schema_editor() as editor:
            operation.database_backwards('tests', editor, new_state, project_state)
        self.assertTableNotExists('i_love_ponies')

    def test_sql_create_function(self):
        project_state = self.set_up_test_model()

        operation = migrations.RunSQL(
            sql='CREATE FUNCTION das_func () RETURNS INTEGER AS $$ BEGIN RETURN 1; END $$ LANGUAGE plpgsql',
            reverse_sql='DROP FUNCTION das_func()'
        )
        new_state = project_state.clone()
        operation.state_forwards('tests', new_state)

        with connection.schema_editor() as editor:
            operation.database_forwards('tests', editor, new_state, project_state)

        with connection.schema_editor() as editor:
            operation.database_backwards('tests', editor, project_state, new_state)

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

        Pony = project_state.apps.get_model('tests', 'Pony')

        @all_schemata
        def pony_count(count, **kwargs):
            found = Pony.objects.count()
            self.assertEqual(
                count,
                found,
                'Incorrect number of Ponies found in schema '
                '{schema}: expected {0}, found {1}'.format(count, found, **kwargs)
            )

        pony_count(0)

        with connection.schema_editor() as editor:
            operation.database_forwards('tests', editor, project_state, new_state)

        pony_count(2)

        with connection.schema_editor() as editor:
            operation.database_backwards('tests', editor, new_state, project_state)

        pony_count(0)

    def test_zero_migration_function(self):
        project_state = self.set_up_test_model()
        Pony = project_state.apps.get_model('tests', 'Pony')

        remove_all_schemata = getattr(
            __import__('boardinghouse.migrations.0001_initial').migrations,
            '0001_initial').remove_all_schemata

        with connection.schema_editor() as editor:
            remove_all_schemata(apps, editor)

        Schema.objects.get(schema='a').activate()
        Pony.objects.all()

    def test_custom_migration_operation(self):
        project_state = self.set_up_test_model()
        operation = AddField(
            app_label='tests',
            model_name='pony',
            name='yellow',
            field=models.BooleanField(default=True)
        )
        new_state = project_state.clone()
        operation.state_forwards('tests', new_state)

        self.assertColumnNotExists('tests_pony', 'yellow')
        with connection.schema_editor() as editor:
            operation.database_forwards('tests', editor, project_state, new_state)

        self.assertColumnExists('tests_pony', 'yellow')
        with connection.schema_editor() as editor:
            operation.database_backwards('tests', editor, new_state, project_state)

        self.assertColumnNotExists('tests_pony', 'yellow')

    def test_constraint_name_method(self):
        from ..models import AwareModel, NaiveModel, SelfReferentialModel

        with connection.schema_editor() as editor:
            six.assertCountEqual(
                self,
                ['tests_awaremodel_pkey'],
                editor._constraint_names(AwareModel, primary_key=True)
            )
            six.assertCountEqual(self, [
                'tests_awaremodel_pkey',
                'tests_awaremodel_name_key'
            ], editor._constraint_names(AwareModel, unique=True))
            six.assertCountEqual(self, [
                'tests_awaremodel_name_key'
            ], editor._constraint_names(AwareModel, unique=True, primary_key=False))
            six.assertCountEqual(self, ['tests_awaremodel_pkey'], editor._constraint_names(AwareModel, primary_key=True, unique=True))
            six.assertCountEqual(self, [], editor._constraint_names(AwareModel, foreign_key=True))
            six.assertCountEqual(self, [], editor._constraint_names(AwareModel, foreign_key=True, primary_key=True))
            six.assertCountEqual(self, ['tests_awaremodel_factor_check'], editor._constraint_names(AwareModel, check=True))

        with connection.schema_editor() as editor:
            six.assertCountEqual(self, ['tests_naivemodel_pkey'], editor._constraint_names(NaiveModel, primary_key=True))
            six.assertCountEqual(self, ['tests_naivemodel_name_key'], editor._constraint_names(NaiveModel, unique=True, primary_key=False))

        with connection.schema_editor() as editor:
            six.assertCountEqual(self, [
                'tests_selfr_parent_id_50446391_fk_tests_selfreferentialmodel_id'
            ], editor._constraint_names(SelfReferentialModel, foreign_key=True))
