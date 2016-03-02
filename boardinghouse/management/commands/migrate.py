"""
:mod:`boardinghouse.management.commands.migrate`

We wrap the django migrate command to ensure the search path is set to
``public,__template__``, which is a special case used only during DDL
statements.
"""
from django.core.management.commands.migrate import Command

from ...schema import _wrap_command

Command.handle = _wrap_command(Command.handle)
