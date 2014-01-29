"""
:mod:`boardinghouse.management.commands.syncdb`

This wraps the previously installed `syncdb` command to ensure:

* the clone_schema function is installed into the database.
* the ``__template__`` schema is created.
* the search path to ``public,__template__``, which is a special case
  used only during DDL statements.
* when the command is complete, all currently existing schemata in the
  SCHEMA_MODEL table exist as schemata in the database.

"""

from django.core.management.commands.syncdb import Command

try:
    from south.management.commands.syncdb import Command
except ImportError:
    pass

from ...schema import get_schema_model, _wrap_command
Command.handle_noargs = _wrap_command(Command.handle_noargs)
