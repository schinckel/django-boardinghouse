TODO
====

* Add in views for allowing inviting of users (registered or not) into a schema.

* Provide a better error when ``loaddata`` is run without ``--schema``, and an error occurred.

* Use the ``schema`` attribute on serialised objects to load them into the correct schema. I think this is possible.

* Trap exceptions on fetching relationships between `Permission` and other objects (`User`, and `Group`), when the table is not found, and return an empty set. Alternatively, we could listen for new instantiations of `User`, and if no schema is activated, then we could set empty values on the cache keys.

Tests to write
--------------

* Test middleware handling of :exc:`boardinghouse.schema.TemplateSchemaActivated`.

* Ensure get_admin_url (non-schema-aware model) still works.

* Test backwards migration of :class:`boardinghouse.operations.AddField`

* Test :meth:`boardinghouse.schema.get_active_schema_name`

* Test saving a schema clears the global active schemata cache

User.visible_schemata property testing:

* Test adding schemata to a user clears the cache.
* Test removing schemata from a user clears the cache.
* Test adding users to schema clears the cache.
* Test removing users from a schema clears the cache.
* Test saving a schema clears the cache for all associated users.


* Test admin with different BOARDINGHOUSE_SCHEMA_MODEL (coverage)

* Test :class:`django.contrib.admin.models.LogEntry` already having ``object_schema`` attribute. Perhaps this should raise an exception? Maybe a :class:`django.core.checks.Error`?

Example Project
---------------

* include user and log-entry data in fixtures
* write some non-admin views and templates
