from django.core.management.commands import loaddata
from django.core.management.base import CommandError

from optparse import make_option

from ...models import Schema, template_schema

class Command(loaddata.Command):
    option_list = loaddata.Command.option_list + (
        make_option('--schema', action='store', dest='schema',
            help='Specify which schema to load schema-aware models to',
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
        
        schema.activate()
        
        data = super(Command, self).handle(*app_labels, **options)
        
        schema.deactivate()
        
        return data