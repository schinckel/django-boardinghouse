"""
:mod:`boardinghouse.management.commands.loaddata`

This replaces the ``loaddata`` command with one that takes a new
option: ``--schema``. This is required when non-shared-models are
included in the file(s) to be loaded, and the schema with this name
will be used as a target.

After completing the load, we ensure that any schemata that were
loaded as part of this process exist as schemata in the database.
"""
import django
from django.core.management.commands import loaddata
from django.core.management.base import CommandError
from django.db import DatabaseError

from optparse import make_option

from ...schema import get_schema_model, _create_all_schemata

class Command(loaddata.Command):
    if django.VERSION < (1, 8):
        option_list = loaddata.Command.option_list + (
            make_option('--schema', action='store', dest='schema',
                help='Specify which schema to load schema-aware models to',
            ),
        )

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument('--schema', action='store', dest='schema',
             help='Specify which schema to load schema-aware models to',
        )

    def handle(self, *app_labels, **options):
        Schema = get_schema_model()

        schema_name = options.get('schema')
        if schema_name == '__template__':
            # Hmm, we don't want to accidentally write data to this, so
            # we should raise an exception if we are going to be
            # writing any schema-aware objects.
            schema = None
        elif schema_name:
            try:
                schema = Schema.objects.get(schema=options.get('schema'))
            except Schema.DoesNotExist:
                raise CommandError('No Schema found named "%s"' % schema_name)

            schema.activate()

        # We should wrap this in a try/except, and present a reasonable
        # error message if we think we tried to load data without a schema
        # that required one.
        super(Command, self).handle(*app_labels, **options)

        Schema().deactivate()

        # Ensure we create any schemata that are new.
        # But, we only want to do this if the schema table has been installed.
        _create_all_schemata()