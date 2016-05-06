Release Notes
=============

0.4.0
-----

:class:`boardinghouse.contrib.template.models.SchemaTemplate` support.

Change the mechanism of applying migrations to use signals instead of hard-coding. This allows for multiple schema models (ie, templates).

Remove no-longer-required flush/migrate overrides for management commands.

Fix swappable schema model.

Update the ``clone_schema()`` database function.




0.3.5
-----

Use migrations instead of running db code immediately. This is for creating the ``__template__`` schema, and installing the ``clone_schema()`` database function.

Rely on the fact that ``settings.BOARDINGHOUSE_SCHEMA_MODEL`` is always set, just to a default if not explicitly set. Same deal for ``settings.PUBLIC_SCHEMA``.

Use a custom subclass of ``migrations.RunSQL`` to allow us to pass extra data to the statement that creates the ``protect_schema_column()`` database function.

Include version numbers in SQL file names.

Move schema creation to a post-save signal, and ensure this signal fires when using ``Schema.objects.bulk_create()``.

Register signal handlers in a more appropriate manner (ie, not in ``models.py``).

Update admin alterations to suit new CSS.

Improve tests and documentation.