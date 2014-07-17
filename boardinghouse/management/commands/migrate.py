"""
:mod:`boardinghouse.management.commands.migrate`

We wrap the django migrate command to ensure:

* the clone_schema function is installed into the database.
* the ``__template__`` schema is created.
* the search path to ``public,__template__``, which is a special case
  used only during DDL statements.
* when the command is complete, all currently existing schemata in the
  SCHEMA_MODEL table exist as schemata in the database.

TODO: Do this as a migration!

"""
from django.core.management.commands.migrate import Command

from ...schema import _wrap_command

Command.handle = _wrap_command(Command.handle)
