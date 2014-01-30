"""
:mod:`boardinghouse.management.commands.migrate`
    
If south is installed, then Migrator class is patched so the following
happens:

* In the case of a SchemaMigration, which should be _only_ using db.*
  api commands, nothing is changed. We rely on the fact that our api
  patching code examines each call, and repeats it for each schema if
  necessary.
* In the case of a DataMigration, we want to run the command N times.
  Technically, this only wants to happen if we are performing the task
  on data that is not part of a shared table.
* We need to prevent the migrator from recording the migration until
  all schemata have been migrated: this is done by replacing the record
  function during the actual migration run, and then swapping it back, and
  calling it.

You will run into problems if your DataMigration contains schema modifying
commands (and vice versa).

You may run into problems if your DataMigration is not idempotent, affects
shared schema models, and you have more than just the __template__ schema.

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

from ...schema import _wrap_command, get_schema_model, get_template_schema

Command = None

try:
    from django.core.management.commands.migrate import Command
except ImportError:
    # South migrations that use the db api should all work. This should
    # be the case for 
    try:
        from south.management.commands.migrate import Command
    except ImportError:
        pass
    else:
        
        from south.migration.migrators import Migrator
        from south.v2 import DataMigration
        
        def wrap(function):
            def apply_to_all(self, migration, database):
                if isinstance(migration.migration_instance(), DataMigration):
                    # Prevent the migration being recorded until we have
                    # done all schemata.
                    record = self.record
                    self.record = lambda migration,database: None
                    for schema in get_schema_model().objects.all():
                        schema.activate()
                        function(self, migration, database)
                    self.record = record
                    get_template_schema().activate()
                    function(self, migration, database)
                else:
                    function(self, migration, database)
            return apply_to_all
        
        Migrator.run = wrap(Migrator.run)
        
else:
    Command.handle = _wrap_command(Command.handle)
