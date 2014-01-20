from django.core.management.commands import dumpdata
from django.core.management.base import CommandError
from django.db.models import get_model

from optparse import make_option

from ...models import Schema, template_schema

class Command(dumpdata.Command):
    option_list = dumpdata.Command.option_list + (
        make_option('--schema', action='store', dest='schema',
            help='Specify which schema to dump schema-aware models from',
            default='__template__',
        ),
    )
    
    def handle(self, *app_labels, **options):
        schema_name = options.get('schema')
        if schema_name == '__template__':
            schema = template_schema
        else:
            try:
                schema = Schema.objects.get(schema=options.get('schema'))
            except Schema.DoesNotExist:
                raise CommandError('No Schema found named "%s"' % schema_name)

        # If we have have any explicit models that are aware, then we should
        # raise an exception if we weren't handed a schema.
        aware_required = any([
            get_model(*label.split('.'))._is_schema_aware
            for label in app_labels if '.' in label
            and get_model(*label.split('.'))
        ])
        
        if aware_required and schema == template_schema:
            raise CommandError('You must pass a schema when an explicit model is aware.')
        
        schema.activate()
        data = super(Command, self).handle(*app_labels, **options)
        schema.deactivate()

        return data