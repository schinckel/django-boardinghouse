from django.core.management.commands.flush import Command
from django.db import connection

from boardinghouse.schema import _wrap_command

Command.handle = _wrap_command(Command.handle)