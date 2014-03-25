TODO
====

* Add in views for allowing inviting of users (registered or not) into a schema.

* Provide a better error when ``loaddata`` is run without ``--schema``, and an error occurred.

* Use the ``schema`` attribute on serialised objects to load them into the correct schema. I think this is possible.

* Enable support for django-devserver: we currently get an infinite recursion when both of us are installed.

* Cache schema queryset so we don't have to load it each request. We would need to invalidate this cache when a new schema is added.


Tests to write
--------------

* Test middleware handling of :exc:`boardinghouse.schema.TemplateSchemaActivated`.

* :meth:`boardinghouse.backends.south_backend.DatabaseOperations.add_deferred_sql`

* :meth:`boardinghouse.backends.south_backend.DatabaseOperations.lookup_constraint`, when columns is provided.

* :mod:`boardinghouse.ensure_installation` - this is pretty hard to test automatically without having multiple projects.

* Test :meth:`boardinghouse.models.SchemaQuerySet.inactive`

Example Project
---------------

* include user and log-entry data in fixtures
* write some non-admin views and templates
