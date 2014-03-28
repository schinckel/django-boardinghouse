TODO
====

* Add in views for allowing inviting of users (registered or not) into a schema.

* Provide a better error when ``loaddata`` is run without ``--schema``, and an error occurred.

* Use the ``schema`` attribute on serialised objects to load them into the correct schema. I think this is possible.

Tests to write
--------------

* Test middleware handling of :exc:`boardinghouse.schema.TemplateSchemaActivated`.

* :meth:`boardinghouse.backends.south_backend.DatabaseOperations.add_deferred_sql`

* :meth:`boardinghouse.backends.south_backend.DatabaseOperations.lookup_constraint`, when columns is provided.

* :mod:`boardinghouse.ensure_installation` - this is pretty hard to test automatically without having multiple projects.

* Test :meth:`boardinghouse.models.SchemaQuerySet.inactive`

* Ensure get_admin_url (non-schema-aware model) still works.

User.visible_schemata property testing:

* Test adding schemata to a user clears the cache.
* Test removing schemata from a user clears the cache.
* Test adding users to schema clears the cache.
* Test removing users from a schema clears the cache.
* Test saving a schema clears the cache for all associated users.

* Test saving a schema clears the global active schemata cache


Example Project
---------------

* include user and log-entry data in fixtures
* write some non-admin views and templates
