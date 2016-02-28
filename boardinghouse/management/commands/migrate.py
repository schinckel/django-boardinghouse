"""
:mod:`boardinghouse.management.commands.migrate`

We wrap the django migrate command to ensure:

* the search path to ``public,__template__``, which is a special case
  used only during DDL statements.
* when the command is complete, all currently existing schemata in the
  SCHEMA_MODEL table exist as schemata in the database.

"""
from django.core.management.commands.migrate import Command

from ...schema import _wrap_command

Command.handle = _wrap_command(Command.handle)
