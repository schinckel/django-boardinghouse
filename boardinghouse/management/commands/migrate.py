from django.db import connection

from ...models import template_schema
from ...schema import _install_clone_schema_function

try:
    from django.core.management.commands import migrate
except ImportError:
    """
    We don't need to do anything at this point: our south backend takes
    care of migrations in that case.
    
    We will just set it so that command will get run.
    """
    Command = migrate.Command
else:
        
    class Command(migrate.Command):
        def handle(self, *args, **options):
            _install_clone_schema_function()
            template_schema.create_schema()
            
            cursor = connection.cursor()
            cursor.execute("SET search_path TO public,__template__;")
            
            super(Command, self).handle(*args, **options)