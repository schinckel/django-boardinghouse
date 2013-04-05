Django Multi-Schema
====================

Use Postgres Schemas for multi-tenant applications (or other segmenting).



Philosophy
----------

Some models should be seperated, others should be global.


Users belong to a schema, and when they view a page, it automatically only fetches data that is from their schema.



How it works
------------

There is a special model: ``Schema``. Whenever new instances of this model are created, the system creates a Postgres schema with that name. There is a special ``__template__`` schema, that stores an empty copy of the schema, and the new schema is defined according to that.

Whenever a ``syncdb`` or ``migrate`` happens, we repeat all of the changes to each schema.

Whenever a request comes in, some middleware determines which schema should be active, and sets the postgres ``search_path`` accordingly. Some users may be able to request a different schema to be activated, and if they have the permission, they will then see data from that schema.


Added neat features (hacks)
---------------------------

Admin users can change to view any schema. There is an added selector in the brand bar for this. You will only see items from the currently selected schema in the admin change list views, and you cannot change schema when viewing an object (as ids are unique across schemata).

I've hacked in support in admin.LogEntry to store the schema on a log when there is a schema associated with the model. The links that are generated (that you see in the recent actions, for instance) contain a url fragment to switch to the correct schema, so they still work.


``./manage.py dumpdata`` and ``loaddata`` gain a ``--schema`` keyword. It defaults to ``__template__``, which is a special empty template. Data will only be dumped-from/loaded-to the selected schema (or public, if the objects are not schema-aware). Data will _not_ be written to ``__template__``, instead an error will be thrown.


TODOs
-----

* Cache schema queryset so we don't have to load it each request.

* Provide a better error when loaddata is run without --schema, and an error occurred.
  
* Use the ``schema`` attribute on serialised objects to load them into the correct schema. I think this is possible.
  