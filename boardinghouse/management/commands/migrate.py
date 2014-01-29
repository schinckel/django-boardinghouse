"""
:mod:`boardinghouse.management.commands.migrate`
    
If south is installed, then the south migrate command is left untouched.

If django 1.7 or greater is installed, we wrap the django migrate
command to ensure:

* the clone_schema function is installed into the database.
* the ``__template__`` schema is created.
* the search path to ``public,__template__``, which is a special case
  used only during DDL statements.
* when the command is complete, all currently existing schemata in the
  SCHEMA_MODEL table exist as schemata in the database.
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
