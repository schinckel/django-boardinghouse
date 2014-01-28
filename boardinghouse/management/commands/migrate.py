"""
Override migrate command for django-boardinghouse.

Will apply the 

"""
from django.db import connection

from ...schema import _wrap_command

try:
    from django.core.management.commands.migrate import Command
except ImportError:
    # We don't need to do anything at this point: our south backend takes
    # care of migrations in that case.
    # 
    # We will just set it so that command will get run.
    try:
        from south.management.commands.migrate import Command
    except ImportError:
        pass
else:
    Command.handle = _wrap_command(Command.handle)