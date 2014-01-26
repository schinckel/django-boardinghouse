TODO
====

* Cache schema queryset so we don't have to load it each request. We would need to invalidate this cache when a new schema is added.

* Cache request.user.schemata queryset (as above).

* Provide a better error when ``loaddata`` is run without ``--schema``, and an error occurred.

* Use the ``schema`` attribute on serialised objects to load them into the correct schema. I think this is possible.

* Create an example project (maybe part of tests?)

* Enable support for django-devserver: we currently get an infinite recursion when both of us are installed.

* Prevent admin access to pages requiring schema selection when no schema is selected.

* Bounce to a reasonable page when a schema change event is processed, and the current page is no longer valid in the new schema. For instance, if viewing schema aware data at:

    https://example.com/photos/223/

  And then changing schema, it probably should show the list of photos, rather than photo with that id in the new schema.

Tests to write
--------------

* Test middleware handling of :py:exception:`TemplateSchemaActivated`.

* :py:method:`boardinghouse.backends.south_backend.DatabaseOperations.add_deferred_sql`

* :py:method:`boardinghouse.backends.south_backend.DatabaseOperations.lookup_constraint`, when columns is provided.

* :py:mod:`boardinghouse.ensure_installation` - this is pretty hard to test automatically without having multiple projects.