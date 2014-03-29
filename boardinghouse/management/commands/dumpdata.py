"""
:mod:`boardinghouse.management.commands.dumpdata`

Replaces the ``dumpdata`` command.

If the ``--schema`` option is supplied, that schema is used for the
source of the data. If it is not supplied, then the ``__template__``
schema will be used (which will not contain any data).

If any models are supplied as arguments (using the ``app_label.model_name`` 
notation) that are not shared models, it is an error to fail to pass a schema.
"""
from django.core.management.commands import dumpdata
from django.core.management.base import CommandError
from django.db import models

from optparse import make_option

from ...schema import (
    is_shared_model, get_active_schemata, 
    activate_schema, activate_template_schema, deactivate_schema,
    Forbidden,
)

class Command(dumpdata.Command):
    option_list = dumpdata.Command.option_list + (
        make_option('--schema', action='store', dest='schema',
            help='Specify which schema to dump schema-aware models from',
            default='__template__',
        ),
    )
    
    def handle(self, *app_labels, **options):
        schema_name = options.get('schema')

        # If we have have any explicit models that are aware, then we should
        # raise an exception if we weren't handed a schema.
        get_model = models.get_model
        aware_required = any([
            not is_shared_model(get_model(*label.split('.')))
            for label in app_labels if '.' in label
            and get_model(*label.split('.'))
        ])

        if schema_name == '__template__':
            if aware_required:
                raise CommandError('You must pass a schema when an explicit model is aware.')
            activate_template_schema()
        else:
            try:
                activate_schema(schema_name)
            except Forbidden:
                raise CommandError('No Schema found named "%s"' % schema_name)
        
        data = super(Command, self).handle(*app_labels, **options)
        
        deactivate_schema()

        return data
