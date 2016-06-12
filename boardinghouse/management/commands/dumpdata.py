"""
:mod:`boardinghouse.management.commands.dumpdata`

Replaces the ``dumpdata`` command.

If the ``--schema`` option is supplied, that schema is used for the
source of the data. If it is not supplied, then the ``__template__``
schema will be used (which will not contain any data).

If any models are supplied as arguments (using the ``app_label.model_name``
notation) that are not shared models, it is an error to fail to pass a schema.
"""
from optparse import make_option

import django
from django.apps import apps
from django.core.management.commands import dumpdata

from ...exceptions import SchemaRequiredException

from ...schema import (
    activate_schema,
    deactivate_schema,
    is_shared_model,
)


class Command(dumpdata.Command):
    if django.VERSION < (1, 8):
        option_list = dumpdata.Command.option_list + (
            make_option('--schema', action='store', dest='schema',
                help='Specify which schema to dump schema-aware models from'),
        )

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument('--schema', action='store', dest='schema',
             help='Specify which schema to dump schema-aware models from')

    def handle(self, *app_labels, **options):
        schema_name = options.get('schema')

        # If we have have any explicit models that are aware, then we should
        # raise an exception if we weren't handed a schema.
        schema_required = []
        for label in app_labels:
            if '.' in label:
                model = apps.get_model(label)
                if not is_shared_model(model):
                    schema_required.append(model)
            else:
                schema_required.extend([
                    model for model in apps.get_app_config(label).get_models()
                    if not is_shared_model(model)
                ])

        if schema_required:
            # Only bother about activating when we actually need to!
            if schema_name:
                activate_schema(schema_name)
            else:
                raise SchemaRequiredException('You must pass a schema when an explicit model is aware: {0}'.format(
                    [x.__name__ for x in schema_required]
                ))

        data = super(Command, self).handle(*app_labels, **options)

        if schema_required:
            deactivate_schema()

        return data
